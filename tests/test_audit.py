import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from pdf_compression_claim_audit.audit import audit, evidence
from pdf_compression_claim_audit.phrases import PDFCOMPRESSION, NOPDFCOMPRESSION, GENERIC_NAMES

EXPECTED = (('compress pdf', 'compresses pdf', 'compressing pdf', 'compress pdfs', 'compresses pdfs', 'compressing pdfs', 'pdf compression', 'pdf compressions', 'compress pdf document', 'compresses pdf document', 'compressing pdf document', 'compress pdf file', 'compresses pdf file', 'compressing pdf file', 'reduce pdf size', 'reduces pdf size', 'reducing pdf size', 'shrink pdf', 'shrinks pdf', 'shrinking pdf', 'optimize pdf', 'optimizes pdf', 'optimizing pdf', 'compress pdf page', 'compresses pdf page', 'compressing pdf page', 'compress pdf pages', 'compresses pdf pages', 'compressing pdf pages', 'make pdf smaller', 'makes pdf smaller', 'making pdf smaller', 'reduce size of pdf', 'reduces size of pdf', 'reducing size of pdf', 'pdf size reduction', 'optimize pdf size', 'optimizes pdf size', 'optimizing pdf size', 'pdf optimizer', 'reduce pdf file size', 'reduces pdf file size', 'reducing pdf file size', 'optimize pdf file size', 'optimizes pdf file size', 'optimizing pdf file size', 'compress pdf content', 'compresses pdf content', 'compressing pdf content', 'shrink pdf file'), ('no pdf compression', 'does not compress pdf', 'does not compress pdfs', 'does not compress pdf document', 'does not compress pdf file', 'does not reduce pdf size', 'does not shrink pdf', 'does not optimize pdf', 'does not make pdf smaller', 'does not reduce size of pdf', 'does not optimize pdf size', 'does not compress pdf page', 'does not compress pdf pages', 'does not reduce pdf file size', 'does not optimize pdf file size', 'does not compress pdf content', 'does not shrink pdf file', 'no pdf compressions', 'does not support pdf compression', 'without pdf compression', 'pdf compression not supported', 'no pdf compression support', 'pdf compression not available', 'no pdf optimizer'), ('compress_pdf', 'compress_pdfs', 'compress_pdf_document', 'compress_pdf_file', 'compress_pdf_page', 'compress_pdf_pages', 'optimize_pdf', 'optimize_pdfs', 'optimize_pdf_document', 'optimize_pdf_file', 'optimize_pdf_size', 'reduce_pdf_size', 'reduce_pdf_file_size', 'shrink_pdf', 'shrink_pdfs', 'make_pdf_smaller', 'reduce_size_of_pdf', 'compress_pdf_content', 'optimize_pdf_content', 'shrink_pdf_file', 'compress_pdf_stream', 'optimize_pdf_stream', 'pdf_compress', 'pdf_optimize'))

class AuditTests(unittest.TestCase):
    def test_oracle(self):
        self.assertEqual((PDFCOMPRESSION, NOPDFCOMPRESSION, GENERIC_NAMES), EXPECTED)

    def test_routes(self):
        examples = [
            'from pypdf import PdfReader as R; R(); p.compress_content_streams()',
            'import pypdf as p; p.PdfWriter(); x.compress_content_streams()',
            'from PyPDF2 import PdfReader; PdfReader(); x.compress_content_streams()',
            'import PyPDF2; PyPDF2.PdfWriter(); x.compress_content_streams()',
            'import pypdf; reader=pypdf.PdfReader(); p=reader.pages[0]; p.compress_content_streams()',
            'from pikepdf import open as op; op(); x.save(compress_streams=True)',
            'import pikepdf; pikepdf.open(); x.save(compress_streams=True)',
            'import pikepdf; pikepdf.Pdf.open(); x.save(object_stream_mode=ObjectStreamMode.generate)',
            'import pikepdf; pikepdf.open(); x.save(recompress_flate=True)',
            'from fitz import open as op; op(); x.save(deflate=True)',
            'import fitz; fitz.open(); x.save(garbage=4)',
            'import pymupdf; pymupdf.Document(); x.save(clean=True)',
            'import fitz; fitz.open(); x.subset_fonts()',
            'from other import compress_pdf as c; c()',
        ]
        examples += ['import pymupdf; pymupdf.open(); x.save(%s=1)' % kw for kw in ('use_objstms','compression_effort','deflate_images','deflate_fonts')]
        examples += ['x.%s()' % name for name in GENERIC_NAMES]
        for source in examples:
            with self.subTest(source=source): self.assertTrue(evidence(source))

    def test_non_routes(self):
        examples = ['import '+x for x in ('pypdf','PyPDF2','pikepdf','fitz','pymupdf','reportlab','gzip','zlib','bz2','lzma')]
        examples += ['import pypdf; pypdf.PdfReader()', 'x.compress_content_streams()', 'import pikepdf; pikepdf.open()', 'x.save(compress_streams=True)', 'x.subset_fonts()']
        examples += ['import pikepdf; pikepdf.open(); x.save('+x+')' for x in ('', 'compress_streams=False', 'object_stream_mode=ObjectStreamMode.preserve', 'linearize=True')]
        examples += ['import fitz; fitz.open(); x.'+x for x in ('save()', 'save(deflate=0,garbage=0,clean=0)', 'save(deflate=False)', 'save(encryption=1)', 'save(linear=True)', 'scrub()', 'set_rotation(90)', 'show_pdf_page()', 'insert_text(rotate=90)', 'add_redact_annot()')]
        examples += ['import pypdf; pypdf.PdfWriter(); x.'+x+'()' for x in ('append','add_page','encrypt','update_page_form_field_values','rotate','merge_page')]
        examples += ['import '+x+'; '+x+'.compress(b"x")' for x in ('gzip','zlib','bz2','lzma')]
        examples += ['import subprocess; subprocess.run(["qpdf"])', 'import subprocess; subprocess.run(["gs"])', 'import subprocess; subprocess.run(["pdfsizeopt"])', 'def compress_pdf(): pass\nx.compress_pdf()', 'from pypdf import PdfReader\nPdfReader=1\nPdfReader(); x.compress_content_streams()', 'import fitz\nwith x as fitz: pass\nfitz.open(); x.subset_fonts()', 'compress_pdf()', 'import fitz; fitz.open(); x.save(deflate="yes")']
        examples += ['pdfplumber.open()', 'pdfminer.extract_text()', 'mindee.parse(InvoiceV4)', 'azure.begin_analyze_document("prebuilt-read")', 'veryfi.Client()', 'documentai.process_document()', 'textract.analyze_document()', 'eden.universal_ai()', 'llamaparse.parse()', 'nanonets.ocr(model_id=opaque)', 'docsumo.upload()', 'pyhanko.sign_pdf()']
        for source in examples:
            with self.subTest(source=source): self.assertFalse(evidence(source))

    def test_findings_and_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); doc=root/'README.md'; src=root/'app.py'
            doc.write_text('compress pdf'); self.assertEqual(audit(root)['findings'][0]['severity'], 'HIGH')
            src.write_text('x.compress_pdf()'); self.assertEqual(audit(root)['verdict'], 'PASS')
            doc.write_text('does not compress pdf'); self.assertEqual(audit(root)['findings'][0]['rule'], 'documented-no-pdf-compression-claim-false')
            src.unlink(); self.assertEqual(audit(root)['verdict'], 'PASS')
            doc.write_text('```\ncompress pdf\n```'); self.assertEqual(audit(root)['verdict'], 'PASS')
            doc.write_text('`compress pdf`'); self.assertEqual(audit(root)['verdict'], 'FAIL')
            (root/'tests').mkdir(); (root/'tests'/'test_x.py').write_text('x.compress_pdf()')
            self.assertEqual(audit(root)['findings'][0]['severity'], 'MEDIUM')
            self.assertEqual(audit(root)['verdict'], 'PASS'); self.assertEqual(audit(root, fail_on='medium')['verdict'], 'FAIL')
            doc.write_text('Nothing claimed'); self.assertEqual(audit(root)['verdict'], 'PASS')

    def test_split_and_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'README.md').write_text('compress pdf')
            (root/'a.py').write_text('import fitz; fitz.open()')
            (root/'b.py').write_text('x.subset_fonts()')
            self.assertEqual(audit(root)['verdict'], 'FAIL')
            (root/'b.py').write_text('x.compress_pdf()')
            (root/'link.py').symlink_to(root/'b.py'); (root/'b.py').unlink()
            self.assertEqual(audit(root)['verdict'], 'FAIL')

    def test_cli(self):
        v=subprocess.run([sys.executable, '-m', 'pdf_compression_claim_audit', '--version'], capture_output=True, text=True)
        self.assertEqual(v.stdout.strip(), '0.1.0')
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp,'README.md').write_text('compress pdf')
            p=subprocess.run([sys.executable,'-m','pdf_compression_claim_audit','audit',tmp,'--json'], capture_output=True, text=True)
            self.assertEqual(p.returncode,2); self.assertEqual(json.loads(p.stdout)['verdict'],'FAIL'); self.assertTrue(json.loads(p.stdout)['findings'][0]['message'])

if __name__ == '__main__': unittest.main()
