import os
import json
import re
import ast
import textwrap
from models.schemas import ReviewResult, Issue

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

PROMPT_TEMPLATE = """You are an expert code reviewer. Analyze the following {language} code and return ONLY a valid JSON object with this exact structure:

{{
  "issues": [
    {{
      "title": "short issue name",
      "severity": "low|medium|high",
      "explanation": "detailed explanation of the problem",
      "suggested_fix": "specific actionable fix",
      "line_number": <1-based integer line number where the issue occurs, or null>
    }}
  ],
  "overall_quality": "Poor|Needs Improvement|Fair|Good|Excellent",
  "summary": "2-3 sentence overall assessment",
  "improved_code": "the full improved version of the code with all fixes applied"
}}

Rules:
- Analyze ONLY the code provided. Do not invent issues that are not present.
- severity must be exactly: low, medium, or high
- line_number must be the exact line number where the issue appears, or null if it spans the whole file
- improved_code MUST be a rewritten version of the submitted code with all issues fixed.
  If code is already clean, still return a polished version with type hints, docstrings, etc.
- Return ONLY the JSON, no markdown, no explanation

Code to review:
```{language}
{code}
```"""


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def _find_line(code: str, pattern: str, flags: int = 0) -> int | None:
    """Return 1-based line number of the first regex match, or None."""
    for i, line in enumerate(code.split('\n'), 1):
        if re.search(pattern, line, flags):
            return i
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# PYTHON ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def _check_python_syntax(code: str) -> Issue | None:
    try:
        ast.parse(code)
        return None
    except SyntaxError as e:
        return Issue(
            title="Syntax error",
            severity="high",
            explanation=f"The code cannot be parsed and will not run: {e.msg}. "
                        f"Python expected something different near: {repr(e.text.strip()) if e.text else 'this line'}.",
            suggested_fix="Fix the syntax error first. Common causes: missing quotes around strings, "
                          "calling a function that does not exist, unmatched parentheses, or typos in keywords.",
            line_number=e.lineno
        )


def _check_python_undefined_names(code: str) -> list[Issue]:
    BUILTINS = {
        "print", "len", "range", "int", "str", "float", "list", "dict", "set",
        "tuple", "bool", "type", "input", "open", "enumerate", "zip", "map",
        "filter", "sorted", "reversed", "sum", "min", "max", "abs", "round",
        "isinstance", "issubclass", "hasattr", "getattr", "setattr", "delattr",
        "repr", "id", "hash", "dir", "vars", "help", "any", "all", "next",
        "iter", "callable", "format", "chr", "ord", "hex", "bin", "oct",
        "None", "True", "False", "NotImplemented", "Ellipsis",
        "Exception", "ValueError", "TypeError", "KeyError", "IndexError",
        "AttributeError", "RuntimeError", "StopIteration", "NotImplementedError",
        "OSError", "IOError", "FileNotFoundError", "PermissionError",
        "NameError", "ImportError", "ModuleNotFoundError", "OverflowError",
        "ZeroDivisionError", "AssertionError", "BaseException",
        "self", "cls", "super", "__name__", "__init__", "__main__",
        "__all__", "__doc__", "__file__", "__package__",
    }
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    defined: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            defined.add(node.id)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                defined.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                defined.add(alias.asname or alias.name)
        elif isinstance(node, ast.arg):
            defined.add(node.arg)
        elif isinstance(node, ast.Global):
            for name in node.names:
                defined.add(name)

    first_line: dict[str, int] = {}
    unknown = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            name = node.id
            if (name not in defined and name not in BUILTINS
                    and not name.startswith("_") and name not in unknown):
                unknown.append(name)
                first_line[name] = getattr(node, 'lineno', None)

    unknown = unknown[:3]
    if not unknown:
        return []

    first_unknown_line = first_line.get(unknown[0])
    return [Issue(
        title=f"Undefined name{'s' if len(unknown) > 1 else ''}: {', '.join(f'`{n}`' for n in unknown)}",
        severity="high",
        explanation=f"{'These names are' if len(unknown) > 1 else 'This name is'} used but never defined or "
                    f"imported: {', '.join(unknown)}. This will raise a NameError at runtime.",
        suggested_fix=f"Either define {'them' if len(unknown) > 1 else 'it'} before use, import the right "
                      f"module, or check for a typo.",
        line_number=first_unknown_line
    )]


def _check_python_patterns(code: str) -> list[Issue]:
    issues = []

    if re.search(r"except\s*:", code):
        issues.append(Issue(
            title="Bare except clause",
            severity="medium",
            explanation="A bare `except:` catches every possible exception including KeyboardInterrupt "
                        "and SystemExit. This makes it impossible to stop the program with Ctrl+C and "
                        "hides bugs that should surface as real errors.",
            suggested_fix="Replace `except:` with `except Exception as e:` and log or re-raise the error "
                          "so failures are visible rather than silently discarded.",
            line_number=_find_line(code, r"except\s*:")
        ))

    if (re.search(r'["\'].*SELECT.*\+\s*\w', code, re.IGNORECASE)
            or re.search(r'execute\s*\(["\'].*\+', code)
            or re.search(r'f["\'].*SELECT.*\{', code, re.IGNORECASE)
            or re.search(r'["\'].*WHERE.*\+', code, re.IGNORECASE)):
        sql_line = (
            _find_line(code, r'["\'].*SELECT.*\+\s*\w', re.IGNORECASE)
            or _find_line(code, r'execute\s*\(["\'].*\+')
            or _find_line(code, r'["\'].*WHERE.*\+', re.IGNORECASE)
        )
        issues.append(Issue(
            title="SQL injection vulnerability",
            severity="high",
            explanation="The SQL query is built by concatenating or formatting user input directly into "
                        "the query string. An attacker can break out of the string and run arbitrary SQL, "
                        "reading or deleting any data in the database.",
            suggested_fix="Use parameterised queries and never interpolate user data into SQL strings:\n"
                          "  cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
            line_number=sql_line
        ))

    if "def " in code and not re.search(r"def \w+\(.*\)\s*->", code):
        issues.append(Issue(
            title="Missing return type hints",
            severity="low",
            explanation="None of the functions declare a return type. Type hints are free documentation "
                        "and allow tools like mypy and your IDE to catch type errors before runtime.",
            suggested_fix="Add `-> ReturnType` to each function signature. "
                          "Use `-> None` for functions that return nothing, "
                          "`-> dict` or a specific TypedDict for data functions.",
            line_number=_find_line(code, r"^\s*def ")
        ))

    if "def " in code and '"""' not in code and "'''" not in code:
        issues.append(Issue(
            title="Missing docstrings",
            severity="low",
            explanation="Functions have no docstrings. Anyone reading this code later "
                        "(including you in three months) will have to read the full body to understand what each function does.",
            suggested_fix='Add a one-line docstring immediately after `def`:\n'
                          '  def my_func(x):\n      """Return x doubled."""\n      return x * 2',
            line_number=_find_line(code, r"^\s*def ")
        ))

    return issues


# ═══════════════════════════════════════════════════════════════════════════════
# JAVASCRIPT ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def _check_javascript(code: str) -> list[Issue]:
    issues = []

    if re.search(r"\bvar\b", code):
        issues.append(Issue(
            title="var instead of const or let",
            severity="medium",
            explanation="`var` declarations are hoisted to function scope and can be accidentally "
                        "re-declared, leading to bugs that are very hard to trace. Modern JavaScript "
                        "has not needed `var` since ES6 (2015).",
            suggested_fix="Replace every `var` with `const` if the value never changes, "
                          "or `let` if it does. Your linter can autofix this.",
            line_number=_find_line(code, r"\bvar\b")
        ))

    if re.search(r"\.then\(", code) and not re.search(r"\.catch\(", code):
        issues.append(Issue(
            title="Unhandled promise rejection",
            severity="high",
            explanation="This promise chain has no `.catch()` handler. If the async operation fails, "
                        "the error is silently swallowed. In Node.js 15+ this crashes the process; "
                        "in browsers it leaves the UI in a broken state.",
            suggested_fix="Add `.catch(err => console.error('Failed:', err))` at the end of the chain, "
                          "or convert to async/await and wrap in try/catch.",
            line_number=_find_line(code, r"\.then\(")
        ))

    if re.search(r"[^=!]==[^=]", code) and not re.search(r"===", code):
        issues.append(Issue(
            title="Loose equality with ==",
            severity="medium",
            explanation="The `==` operator performs type coercion before comparing. "
                        "This causes surprising results: `0 == ''` is `true`, `null == undefined` is `true`. "
                        "This is one of the most common sources of subtle JavaScript bugs.",
            suggested_fix="Always use `===` (strict equality) and `!==` (strict inequality). "
                          "ESLint's `eqeqeq` rule can enforce this automatically.",
            line_number=_find_line(code, r"[^=!]==[^=]")
        ))

    if re.search(r"console\.log\(", code):
        issues.append(Issue(
            title="console.log left in code",
            severity="low",
            explanation="Debug logging left in production code can expose sensitive data in the browser console "
                        "and adds unnecessary noise.",
            suggested_fix="Remove debug `console.log` calls before shipping. "
                          "Use a proper logger library (e.g. pino, winston) that can be silenced in production.",
            line_number=_find_line(code, r"console\.log\(")
        ))

    if re.search(r"\w+\.\w+\.\w+", code) and not re.search(r"\?\.", code):
        issues.append(Issue(
            title="Deep property access without optional chaining",
            severity="medium",
            explanation="Accessing nested properties like `a.b.c` will throw a TypeError if any intermediate "
                        "value is null or undefined. This is extremely common in API response handling.",
            suggested_fix="Use optional chaining: `a?.b?.c` returns `undefined` instead of throwing. "
                          "Combine with nullish coalescing for defaults: `a?.b?.c ?? 'default'`",
            line_number=_find_line(code, r"\w+\.\w+\.\w+")
        ))

    return issues


# ═══════════════════════════════════════════════════════════════════════════════
# JAVA ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def _check_java(code: str) -> list[Issue]:
    issues = []

    if re.search(r"catch\s*\(\s*Exception\b", code):
        issues.append(Issue(
            title="Overly broad exception catch",
            severity="medium",
            explanation="Catching `Exception` swallows every possible error — including ones you have "
                        "no idea how to recover from. It makes the codebase brittle and debugging painful.",
            suggested_fix="Catch the specific exception types you expect: `IOException`, `SQLException`, etc. "
                          "Let everything else propagate up to a top-level handler.",
            line_number=_find_line(code, r"catch\s*\(\s*Exception\b")
        ))

    if re.search(r"new\s+\w+(Stream|Reader|Writer|Connection)\b", code) and not re.search(r"try\s*\(", code):
        issues.append(Issue(
            title="Resource leak risk",
            severity="high",
            explanation="Streams and connections opened without try-with-resources will not be closed "
                        "if an exception is thrown between open and close. Over time this exhausts "
                        "file handles or database connections.",
            suggested_fix="Use try-with-resources which closes automatically:\n"
                          "  try (BufferedReader br = new BufferedReader(new FileReader(path))) {\n"
                          "      // use br\n  }",
            line_number=_find_line(code, r"new\s+\w+(Stream|Reader|Writer|Connection)\b")
        ))

    if re.search(r"\bList\b(?!\s*<)", code) or re.search(r"\bMap\b(?!\s*<)", code):
        raw_line = _find_line(code, r"\bList\b(?!\s*<)") or _find_line(code, r"\bMap\b(?!\s*<)")
        issues.append(Issue(
            title="Raw generic types",
            severity="low",
            explanation="Using raw `List` or `Map` without type parameters bypasses the compiler's "
                        "type checker. You will get unchecked cast warnings and potential ClassCastExceptions at runtime.",
            suggested_fix="Always parameterise generics: `List<String>`, `Map<String, Integer>`. "
                          "If you truly need mixed types, use `List<Object>` explicitly.",
            line_number=raw_line
        ))

    if re.search(r'==\s*"', code) or re.search(r'"\s*==', code):
        str_cmp_line = _find_line(code, r'==\s*"') or _find_line(code, r'"\s*==')
        issues.append(Issue(
            title="String comparison with == instead of .equals()",
            severity="high",
            explanation="In Java, `==` on Strings compares object identity (memory address), not content. "
                        "Two strings with identical text can be different objects, making `==` return false unexpectedly.",
            suggested_fix='Use `.equals()` for content comparison: `if (name.equals("Alice"))`\n'
                          'Or `Objects.equals(a, b)` which is null-safe.',
            line_number=str_cmp_line
        ))

    return issues


# ═══════════════════════════════════════════════════════════════════════════════
# C++ ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def _check_cpp(code: str) -> list[Issue]:
    issues = []

    if re.search(r"\bnew\b", code) and not re.search(r"unique_ptr|shared_ptr|make_unique|make_shared", code):
        issues.append(Issue(
            title="Raw pointer — possible memory leak",
            severity="high",
            explanation="Allocating with `new` and never calling `delete` leaks memory. "
                        "Even if you do call `delete`, an exception between `new` and `delete` "
                        "still causes a leak. Raw `new` is considered bad practice in modern C++.",
            suggested_fix="Replace `new T(...)` with `std::make_unique<T>(...)` or `std::make_shared<T>(...)`. "
                          "The destructor handles deallocation automatically, even when exceptions are thrown.",
            line_number=_find_line(code, r"\bnew\b")
        ))

    if re.search(r"\bstrcpy\b|\bstrcat\b|\bgets\b|\bsprintf\b", code):
        issues.append(Issue(
            title="Unsafe C string functions",
            severity="high",
            explanation="`strcpy`, `gets`, and `sprintf` write to buffers without checking size. "
                        "If the input is longer than the buffer, they overwrite adjacent memory — "
                        "a classic security vulnerability that enables arbitrary code execution.",
            suggested_fix="Use `strncpy`, `strncat`, `snprintf`, or better yet `std::string` which "
                          "manages its own memory and has no fixed-size limitation.",
            line_number=_find_line(code, r"\bstrcpy\b|\bstrcat\b|\bgets\b|\bsprintf\b")
        ))

    if "using namespace std;" in code:
        issues.append(Issue(
            title="using namespace std in global scope",
            severity="low",
            explanation="Importing the entire `std` namespace globally can cause name collisions with "
                        "your own code or other libraries. This is especially dangerous in header files.",
            suggested_fix="Remove `using namespace std;` and use explicit `std::` prefixes. "
                          "If typing `std::` feels verbose, import only what you need: `using std::cout;`",
            line_number=_find_line(code, r"using namespace std;")
        ))

    if re.search(r"for\s*\(.*<=\s*\w+\s*;", code):
        issues.append(Issue(
            title="Off-by-one in loop condition",
            severity="medium",
            explanation="Using `<=` with an array size causes the loop to access one element past "
                        "the end of the array on the final iteration. This is undefined behaviour in C++.",
            suggested_fix="Use `<` instead of `<=` when iterating by index: `for (int i = 0; i < size; i++)`",
            line_number=_find_line(code, r"for\s*\(.*<=\s*\w+\s*;")
        ))

    return issues


# ═══════════════════════════════════════════════════════════════════════════════
# IMPROVED CODE GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

def _build_improved_code(code: str, lang: str, issues: list[Issue]) -> str:
    result = code

    if lang == "python":
        # Fix bare excepts
        result = re.sub(r'\bexcept\s*:', 'except Exception as e:', result)

        # Add missing docstrings to functions that lack them
        def add_docstring(m):
            indent = m.group(1)
            sig = m.group(2)
            body_start = m.group(3)
            if '"""' in body_start or "'''" in body_start:
                return m.group(0)
            func_name = re.search(r'def (\w+)', sig)
            name = func_name.group(1) if func_name else 'this function'
            doc = f'{indent}    """TODO: describe what {name} does."""\n'
            return f"{indent}{sig}{body_start}{doc}"

        result = re.sub(
            r'^( *)( *def [^\n]+:\n)( *(?!"""|\'\'\'))',
            add_docstring,
            result,
            flags=re.MULTILINE
        )

        # Add return type hint comment to functions missing one
        result = re.sub(
            r'def \w+\([^)]*\)\s*:(?!\s*->)',
            lambda m: m.group(0).rstrip(':') + '  # type: add return hint',
            result
        ) if "def " in result and "->" not in result else result

        # Fix SQL injection where we can detect the pattern
        if re.search(r'".*WHERE.*"\s*\+', result):
            result = re.sub(
                r'(["\'])(.+?WHERE\s+\w+\s*=\s*)\1\s*\+\s*(\w+)',
                r'"\2?", (\3,)  # Fixed: use parameterised query',
                result
            )

    elif lang == "javascript":
        result = re.sub(r'\bvar\b', 'const', result)
        result = re.sub(
            r'(\.then\([^)]+\))\s*;',
            r'\1\n  .catch(err => console.error("Error:", err));',
            result
        )
        result = re.sub(r'(?<![=!])={2}(?!=)', '===', result)

    elif lang == "java":
        result = re.sub(r'(\w+)\s*==\s*(".*?")', r'\1.equals(\2)', result)
        result = re.sub(r'(".*?")\s*==\s*(\w+)', r'\1.equals(\2)', result)

    elif lang in ("cpp", "c++"):
        result = result.replace(
            "using namespace std;",
            "// Prefer explicit std:: prefix over 'using namespace std;'"
        )
        result = re.sub(
            r'(for\s*\(.*?;\s*\w+\s*)<=(.*?;)',
            r'\1<\2',
            result
        )

    if result.strip() == code.strip() and issues:
        comment = {"python": "#", "javascript": "//", "java": "//", "cpp": "//"}.get(lang, "//")
        todos = "\n".join(f"{comment} FIXME: {i.title}" for i in issues)
        result = f"{todos}\n\n{code}"

    if result.strip() == code.strip() and not issues:
        comment = {"python": "#", "javascript": "//", "java": "//", "cpp": "//"}.get(lang, "//")
        result = f"{comment} Code reviewed by CodePilot. No issues found.\n{code}"

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# SCORING
# ═══════════════════════════════════════════════════════════════════════════════

def _score(issues: list[Issue]) -> tuple[str, str]:
    high = sum(1 for i in issues if i.severity == "high")
    med  = sum(1 for i in issues if i.severity == "medium")
    n    = len(issues)

    if high >= 2 or (high >= 1 and med >= 1):
        quality = "Poor"
    elif high == 1:
        quality = "Needs Improvement"
    elif med >= 2:
        quality = "Fair"
    elif med == 1 or n >= 2:
        quality = "Good"
    else:
        quality = "Excellent"

    if n == 0:
        summary = "The code looks clean and follows good practices. Nothing to fix here."
    elif n == 1:
        summary = "The code is mostly solid. There is one issue worth addressing before shipping to production."
    else:
        high_label = f"{high} high severity " if high else ""
        summary = (
            f"The review found {n} issues ({high_label}total). "
            f"The improved version below applies all the fixes that can be automated. "
            f"Review the remaining TODOs manually."
        )

    return quality, summary


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

async def analyze_code(code: str, language: str) -> ReviewResult:
    if OPENAI_API_KEY and OPENAI_API_KEY not in ("", "your-key-here"):
        return await _analyze_with_openai(code, language)
    return _analyze_with_mock(code, language)


def _analyze_with_mock(code: str, language: str) -> ReviewResult:
    lang = language.lower().strip()
    issues: list[Issue] = []

    if lang == "python":
        syntax_err = _check_python_syntax(code)
        if syntax_err:
            issues.append(syntax_err)
            quality, summary = _score(issues)
            improved = _suggest_syntax_fix(code)
            return ReviewResult(
                issues=issues,
                overall_quality=quality,
                summary=summary,
                improved_code=improved,
                mode="mock"
            )
        issues += _check_python_undefined_names(code)
        issues += _check_python_patterns(code)

    elif lang == "javascript":
        issues += _check_javascript(code)

    elif lang == "java":
        issues += _check_java(code)

    elif lang in ("cpp", "c++", "cplusplus"):
        issues += _check_cpp(code)

    issues = issues[:5]
    quality, summary = _score(issues)
    improved = _build_improved_code(code, lang, issues)

    return ReviewResult(
        issues=issues,
        overall_quality=quality,
        summary=summary,
        improved_code=improved,
        mode="mock"
    )


def _suggest_syntax_fix(code: str) -> str:
    fixed = code

    fixed = re.sub(
        r'\bprin\b\s*\(([^"\'()]+)\)',
        lambda m: f'print("{m.group(1).strip()}")',
        fixed
    )
    fixed = re.sub(
        r'(\w+)\s*\(([^"\'()\d\[\]{}][^"\'()]*[a-zA-Z!?.][^"\'()]*)\)',
        lambda m: f'{m.group(1)}("{m.group(2).strip()}")'
        if ' ' in m.group(2) or '!' in m.group(2) else m.group(0),
        fixed
    )

    try:
        ast.parse(fixed)
        return f"# CodePilot: syntax corrected\n{fixed}"
    except SyntaxError:
        return f"# CodePilot: syntax error detected — manual fix required\n# See the issue description above\n{code}"


async def _analyze_with_openai(code: str, language: str) -> ReviewResult:
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        prompt = PROMPT_TEMPLATE.format(language=language, code=code)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw.strip())
        issues = [Issue(**i) for i in data.get("issues", [])]
        return ReviewResult(
            issues=issues,
            overall_quality=data.get("overall_quality", "Unknown"),
            summary=data.get("summary", ""),
            improved_code=data.get("improved_code", code),
            mode="ai"
        )
    except Exception as e:
        print(f"OpenAI error, falling back to mock: {e}")
        result = _analyze_with_mock(code, language)
        result.mode = "ai-fallback"
        return result
