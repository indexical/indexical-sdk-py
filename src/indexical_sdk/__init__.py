# Import necessary Python libraries
import json
import re
from typing import Union, Dict, List, Set
from packaging import version as packaging_version


def _min_js_version_helper(spec: str):
    version_parts = [
        re.sub(r"[^.0-9\-]+", "", re.sub(r"[Xx]", "0", v))
        for v in spec.split()
        if re.match(r"[0-9.\-<>\^=~Xx]+", v)
    ]
    try:
        target = min(version_parts, key=packaging_version.parse)
        return target
    except:
        return None


def extract_sources_from_package_json(
    input_data: Union[str, Dict]
) -> Dict[str, List[str]]:
    if isinstance(input_data, str):
        json_data = json.loads(input_data)
    else:
        json_data = input_data

    dependencies: Dict[str, str] = json_data.get("dependencies", {})

    pkgs: List[str] = []
    for pkg, version_spec in dependencies.items():
        target = _min_js_version_helper(version_spec)
        if target is not None:
            pkgs.append(f"{pkg}@{target}")
        else:
            pkgs.append(pkg)

    return {"npm": pkgs}


def extract_sources_from_package_lock_json(
    input_data: Union[str, Dict]
) -> Dict[str, List[str]]:
    if isinstance(input_data, str):
        json_data = json.loads(input_data)
    else:
        json_data = input_data

    packages = json_data.get("packages")
    if not packages:
        raise ValueError("Invalid package-lock.json contents")

    root = packages.get("")
    dependencies = root.get("dependencies", {}).keys()

    npm_dependencies = []
    for dep in dependencies:
        entry = packages.get(dep, packages.get(f"node_modules/{dep}"))
        if entry and entry.get("version"):
            npm_dependencies.append(f"{dep}@{entry['version']}")
        else:
            version_spec = root.get("dependencies", {}).get("dep", "")
            target = _min_js_version_helper(version_spec)
            if target is not None:
                npm_dependencies.append(f"{dep}@{target}")
            else:
                npm_dependencies.append(dep)

    return {"npm": npm_dependencies}


def extract_sources_from_js(input_data: str) -> Dict[str, List[str]]:
    IMPORT_REGEX = re.compile(
        r'import(?:(?:(?:[ \n\t]+(?:[^ *\n\t\{\},]+)[ \n\t]*(?:,|[ \n\t]+))?(?:[ \n\t]*\{(?:[ \n\t]*[^ \n\t"\'\{\}]+[ \n\t]*,?)+\})?[ \n\t]*)|[ \n\t]*\*[ \n\t]*as[ \n\t]+(?:[^ \n\t\{\}]+)[ \n\t]+)from[ \n\t]*(?:[\'"])([^\'"\n]+)(?:[\'"])'
    )
    DYNAMIC_IMPORT_REGEX = re.compile(
        r'(?:\W|^)import\(["\']([^"\']+)["\']\)', re.MULTILINE
    )
    REQUIRE_REGEX = re.compile(r'(?:\W|^)require\(["\']([^"\']+)["\']\)', re.MULTILINE)

    pkgs = set()
    for regex in [IMPORT_REGEX, DYNAMIC_IMPORT_REGEX, REQUIRE_REGEX]:
        for match in regex.finditer(input_data):
            pkg = match.group(1)
            if not pkg.startswith((".", "/")):
                pkgs.add(pkg)

    return {"npm": list(pkgs)}


def extract_sources_from_py(input_data: str) -> Dict[str, List[str]]:
    IMPORT_REGEX = re.compile(
        r"^\s*(?:from|import)\s+([\w.]+(?:\s*,\s*\w+)*)", re.MULTILINE
    )
    pkgs = set()

    for match in IMPORT_REGEX.finditer(input_data):
        pkg_list = match.group(1).split(",")
        for pkg in pkg_list:
            if not pkg.startswith((".", "/")):
                pkg_name = pkg.strip().split(".")[0]
                pkgs.add(pkg_name)
                pkgs.add(pkg_name.replace("_", "-"))

    return {"pypi": list(pkgs)}


def extract_sources_from_requirements_txt(input_data: str) -> Dict[str, List[str]]:
    PACKAGE_LINE_REGEX = re.compile(r"^[A-Za-z0-9]+.*", re.MULTILINE)
    VERSION_SPECIFIER_REGEX = re.compile(r"([=><!]+)\s*([0-9.*]+)")
    PACKAGE_NAME_REGEX = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*[A-Za-z0-9])")

    pkgs = set()
    for pkg_line_match in PACKAGE_LINE_REGEX.finditer(input_data):
        pkg_line = pkg_line_match.group()
        if re.match(r"^[a-z]+:\/\//", pkg_line):
            continue
        pkg_match = PACKAGE_NAME_REGEX.match(pkg_line)
        if pkg_match:
            pkg = pkg_match.group(0)
            if "@" in pkg_line:
                pkgs.add(pkg)
                continue

            target = None
            for match in VERSION_SPECIFIER_REGEX.finditer(pkg_line):
                relation, version = match.groups()
                if relation == "==" or ">" in relation:
                    target = version.replace("*", "0")

            pkgs.add(f"{pkg}@{target}" if target else pkg)

    return {"pypi": list(pkgs)}
