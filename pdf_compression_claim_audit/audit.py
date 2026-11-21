"""Inspect documentation and Python syntax without executing project code."""
import ast
import os
import re
from pathlib import Path
from .phrases import PDFCOMPRESSION, NOPDFCOMPRESSION, GENERIC_NAMES


def normalize(text):
    return ' '.join(text.lower().replace('’', "'").replace("n't", ' not').replace('-', ' ').split())


def pattern(phrases):
    return re.compile(r'\b(?:' + '|'.join(re.escape(p) for p in sorted(phrases, key=lambda p: (-len(p), p))) + r')\b')


def paragraphs(text):
    lines, fence = [], None
    for line in text.splitlines():
        mark = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if fence:
            if re.match(r'^ {0,3}' + re.escape(fence[0]) + '{' + str(len(fence)) + r',}\s*$', line):
                fence = None
            lines.append('')
        elif mark:
            fence = mark.group(1)
            lines.append('')
        else:
            lines.append(line)
    return [normalize(p) for p in re.split(r'\n\s*\n', '\n'.join(lines)) if p.strip()]


def evidence(source):
    try:
        nodes = list(ast.walk(ast.parse(source)))
    except (SyntaxError, ValueError):
        return False
    imports, shadows, definitions = {}, set(), set()
    def names(target):
        if isinstance(target, ast.Name):
            return {target.id}
        if isinstance(target, (ast.Tuple, ast.List)):
            return set().union(*(names(x) for x in target.elts))
        if isinstance(target, ast.Starred):
            return names(target.value)
        return set()
    for node in nodes:
        if isinstance(node, ast.Import):
            for a in node.names:
                imports[a.asname or a.name.split('.')[0]] = a.name if a.asname else a.name.split('.')[0]
        elif isinstance(node, ast.ImportFrom) and not node.level:
            for a in node.names:
                imports[a.asname or a.name] = (node.module or '') + '.' + a.name
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            definitions.add(node.name)
            shadows.add(node.name)
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            targets = [x.optional_vars for x in node.items if x.optional_vars]
        for target in targets:
            shadows.update(names(target))
    reader = pike = mupdf = content = subset = pike_save = mu_save = False
    for node in nodes:
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        resolved = ''
        if isinstance(func, ast.Name):
            if func.id not in shadows:
                resolved = imports.get(func.id, '')
            name = resolved.rsplit('.', 1)[-1]
        elif isinstance(func, ast.Attribute):
            name = func.attr
            base = func.value
            while isinstance(base, ast.Attribute):
                base = base.value
            if isinstance(base, ast.Name):
                if base.id in imports and base.id in shadows:
                    continue
                resolved = imports.get(base.id, '')
        else:
            continue
        if name in definitions:
            continue
        if name in GENERIC_NAMES and (isinstance(func, ast.Attribute) or resolved):
            return True
        if isinstance(func, ast.Name):
            reader |= resolved in {'pypdf.PdfReader', 'pypdf.PdfWriter', 'PyPDF2.PdfReader', 'PyPDF2.PdfWriter'}
            pike |= resolved in {'pikepdf.open', 'pikepdf.Pdf'}
            mupdf |= resolved in {'fitz.open', 'fitz.Document', 'pymupdf.open', 'pymupdf.Document'}
        else:
            reader |= resolved in {'pypdf', 'PyPDF2'} and name in {'PdfReader', 'PdfWriter'}
            pike |= (resolved == 'pikepdf' or resolved == 'pikepdf.Pdf') and name in {'open', 'Pdf'}
            mupdf |= resolved in {'fitz', 'pymupdf'} and name in {'open', 'Document'}
            content |= name == 'compress_content_streams'
            subset |= name == 'subset_fonts'
            if name == 'save':
                for kw in node.keywords:
                    v = kw.value
                    if kw.arg in {'compress_streams', 'recompress_flate'} and isinstance(v, ast.Constant) and v.value is True:
                        pike_save = True
                    if kw.arg == 'object_stream_mode' and ((isinstance(v, ast.Attribute) and v.attr == 'generate') or (isinstance(v, ast.Name) and v.id == 'generate')):
                        pike_save = True
                    if kw.arg in {'deflate', 'deflate_images', 'deflate_fonts', 'garbage', 'clean', 'use_objstms', 'compression_effort'} and isinstance(v, ast.Constant) and isinstance(v.value, int) and bool(v.value):
                        mu_save = True
    return bool((reader and content) or (pike and pike_save) or (mupdf and (mu_save or subset)))


def audit(root, ignore=(), fail_on='high'):
    root = Path(root)
    if not root.is_dir() or not os.access(str(root), os.R_OK | os.X_OK):
        raise OSError('Not a readable directory: {}'.format(root))
    claims = denials = production = tests = False
    yes_re, no_re = pattern(PDFCOMPRESSION), pattern(NOPDFCOMPRESSION)
    for directory, dirs, files in os.walk(str(root), followlinks=False, onerror=lambda e: (_ for _ in ()).throw(e)):
        parent = Path(directory)
        def ignored(path):
            rel = path.relative_to(root).as_posix()
            return any(rel == p.rstrip('/') or rel.startswith(p.rstrip('/') + '/') for p in ignore)
        dirs[:] = sorted(d for d in dirs if not (parent / d).is_symlink() and not ignored(parent / d))
        for filename in sorted(files):
            path = parent / filename
            if path.is_symlink() or ignored(path):
                continue
            rel = path.relative_to(root)
            if (rel.as_posix() == 'README.md' or ('docs' in rel.parts and path.suffix == '.md')):
                for para in paragraphs(path.read_text(encoding='utf-8')):
                    denials |= bool(no_re.search(para))
                    claims |= bool(yes_re.search(no_re.sub(' ', para)))
            if path.suffix == '.py' and not any(x in rel.parts for x in ('fixtures', 'docs', 'examples')):
                is_test = 'tests' in rel.parts or filename.startswith('test_') or filename.endswith('_test.py')
                if evidence(path.read_text(encoding='utf-8')):
                    if is_test:
                        tests = True
                    else:
                        production = True
    findings = []
    if claims and not production:
        severity = 'MEDIUM' if tests else 'HIGH'
        findings.append({'rule': 'documented-pdf-compression-claim-false', 'severity': severity, 'message': 'Documented claim has ' + ('test-only evidence.' if tests else 'no production evidence.')})
    if denials and production:
        findings.append({'rule': 'documented-no-pdf-compression-claim-false', 'severity': 'HIGH', 'message': 'Documented denial conflicts with production evidence.'})
    fail = any(f['severity'] == 'HIGH' or fail_on.lower() == 'medium' for f in findings)
    return {'verdict': 'FAIL' if fail else 'PASS', 'findings': findings}
