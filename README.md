# Documentation claim auditor

An offline static checker compares documentation with Python source. It never executes inspected source or contacts a network.

```text
pdf-compression-claim-audit
compress pdf
compresses pdf
compressing pdf
compress pdfs
compresses pdfs
compressing pdfs
pdf compression
pdf compressions
compress pdf document
compresses pdf document
compressing pdf document
compress pdf file
compresses pdf file
compressing pdf file
reduce pdf size
reduces pdf size
reducing pdf size
shrink pdf
shrinks pdf
shrinking pdf
optimize pdf
optimizes pdf
optimizing pdf
compress pdf page
compresses pdf page
compressing pdf page
compress pdf pages
compresses pdf pages
compressing pdf pages
make pdf smaller
makes pdf smaller
making pdf smaller
reduce size of pdf
reduces size of pdf
reducing size of pdf
pdf size reduction
optimize pdf size
optimizes pdf size
optimizing pdf size
pdf optimizer
reduce pdf file size
reduces pdf file size
reducing pdf file size
optimize pdf file size
optimizes pdf file size
optimizing pdf file size
compress pdf content
compresses pdf content
compressing pdf content
shrink pdf file
no pdf compression
does not compress pdf
does not compress pdfs
does not compress pdf document
does not compress pdf file
does not reduce pdf size
does not shrink pdf
does not optimize pdf
does not make pdf smaller
does not reduce size of pdf
does not optimize pdf size
does not compress pdf page
does not compress pdf pages
does not reduce pdf file size
does not optimize pdf file size
does not compress pdf content
does not shrink pdf file
no pdf compressions
does not support pdf compression
without pdf compression
pdf compression not supported
no pdf compression support
pdf compression not available
no pdf optimizer
documented-pdf-compression-claim-false
documented-no-pdf-compression-claim-false
```

Install from a distribution using pip. Run the audit with the command below; the directory defaults to the current directory. The module entry point is also available.

```sh
pdf-compression-claim-audit audit . --json
python3 -m pdf_compression_claim_audit audit . --fail-on medium --ignore vendor
```

The exit status is 0 for a passing threshold, 2 for findings meeting the threshold, and 1 for usage or I/O errors. Use `--verbose` for details; `--ignore` accepts repeatable relative path prefixes. The default threshold is high. Test-only evidence has medium severity. Documentation consists of the root README and Markdown files under docs; fenced blocks are excluded and inline code is included.

## Matching limitations

- This phrase
  ```
  pdf compression
  ```
  is deliberately a PDFCOMPRESSION phrase: in document-tool docs it almost always names the checked operation. But it can also name a tool that only lists a compression feature in a roadmap, not one that compresses. A doc that means that is a false positive.

- This phrase
  ```
  compress pdf
  ```
  is deliberately a PDFCOMPRESSION phrase: a doc can say it about a class that only wraps a PDF writer and never calls a compression operation.

- This phrase
  ```
  reduce pdf size
  ```
  is deliberately a PDFCOMPRESSION phrase: a doc can say it about deleting pages from a PDF, not about compressing its content streams.

- This phrase
  ```
  shrink pdf
  ```
  is deliberately a PDFCOMPRESSION phrase: a doc can say it about scaling pages down to a smaller page size, not about compressing the file.

- This phrase
  ```
  optimize pdf
  ```
  is deliberately a PDFCOMPRESSION phrase: a doc can say it about reordering pages, not about compressing the file.

- This phrase
  ```
  make pdf smaller
  ```
  is deliberately a PDFCOMPRESSION phrase: a doc can say it about splitting a PDF into smaller files, not about compressing one file.

- This phrase
  ```
  reduce size of pdf
  ```
  is deliberately a PDFCOMPRESSION phrase: a doc can say it about removing pages, not about compressing content.

- This phrase
  ```
  pdf size reduction
  ```
  is deliberately a PDFCOMPRESSION phrase: a doc can say it about a file that is smaller because pages were removed, not because anything was compressed.

- This phrase
  ```
  pdf optimizer
  ```
  is deliberately a PDFCOMPRESSION phrase: a doc can say it about a tool name that only linearizes PDFs for fast web view, not about one that compresses.

- This phrase
  ```
  compress pdf content
  ```
  is deliberately a PDFCOMPRESSION phrase: a doc can say it about zipping the PDF file with gzip, not about compressing the PDF itself.

- This phrase
  ```
  compress pdf page
  ```
  is deliberately a PDFCOMPRESSION phrase: a doc can say it about cropping a page, not about compressing it.

- Pair routes are module-scoped, not variable-scoped: a pypdf / PyPDF2 construction and an unrelated .compress_content_streams call in the same module count as evidence.

- A pypdf / PyPDF2 construction + .compress_content_streams call IS detected even if the compressed page is never saved: the call itself is the compression fingerprint; the tool does not check whether the result is written out.

- A pikepdf opener + .save call with an explicit compression keyword IS detected even if the saved file ends up larger: the keyword itself is the compression fingerprint; the tool does not measure the output size.

- A PyMuPDF opener + .save call with a compression keyword IS detected even if the keyword value is the smallest truthy one (for example garbage=1): any nonzero value selects the operation; the tool does not grade the strength.

- A PyMuPDF opener + .subset_fonts call IS detected even if no font in the document is eligible for subsetting: the call itself is the compression fingerprint; the tool does not check whether any font shrank.

- A generic compression-named call IS detected even if it is called with no arguments: the name itself is the compression fingerprint; the tool does not evaluate the arguments.

- A lone pypdf / PyPDF2 PdfReader / PdfWriter construction with no .compress_content_streams call is NOT detected: a reader or writer that never compresses compresses nothing.

- A bare .compress_content_streams call is NOT detected unless a pypdf / PyPDF2 PdfReader / PdfWriter construction is present in the same module: the method name alone is too generic.

- A lone pikepdf opener call with no .save call is NOT detected: an opener that never saves saves nothing.

- A pikepdf opener + bare .save() call is NOT detected: saving with no explicit compression keyword is copying, not compressing, by design — even though pikepdf's save defaults compress_streams to True, the tool requires the keyword to be explicit.

- A pikepdf opener + .save(compress_streams=False) call is NOT detected: compression was explicitly switched off.

- A pikepdf opener + .save(object_stream_mode=preserve) call is NOT detected: preserving object streams is not generating them.

- A pikepdf opener + .save(linearize=True) call alone is NOT detected: linearization lays a PDF out for fast web view; it does not compress it.

- A lone PyMuPDF opener call with no .save / .subset_fonts call is NOT detected: an opener that never saves or subsets compresses nothing.

- A PyMuPDF opener + .save() call with all compression keywords zero / False is NOT detected: saving with every compression knob at zero is copying, not compressing.

- A PyMuPDF opener + .save() call with an encryption keyword alone is NOT detected: password-protecting a PDF is the R238 family, not compression.

- A PyMuPDF opener + .save(linear=True) call alone is NOT detected: linearization is fast-web-view layout, not compression.

- A PyMuPDF opener + .scrub() call alone is NOT detected: scrubbing is document sanitizing, not compressing.

- A bare .subset_fonts call is NOT detected unless a PyMuPDF opener call is present in the same module: the method name alone is too generic.

- A bare .save call is NOT detected unless a pikepdf or PyMuPDF opener call is present in the same module: the method name alone is too generic.

- gzip / zlib / bz2 / lzma compression of raw bytes is NOT detected: compressing bytes is the general compression family, not the checked operation.

- pikepdf is detected ONLY through an explicit compression keyword on save: a bare save is not detected by design.

- A pypdf / PyPDF2 PdfWriter + append / merge call is NOT detected: appending or merging whole files is the R236 merge route, not compression.

- A pypdf / PyPDF2 PdfWriter + add_page call is NOT detected: adding pages is the R237 split route, not compression.

- A pypdf / PyPDF2 PdfWriter + encrypt call is NOT detected: encrypting a PDF is the R238 family, not compression.

- A pypdf / PyPDF2 PdfReader / PdfWriter + rotate call is NOT detected: rotating pages is the R239 family, not compression.

- A PyMuPDF opener + set_rotation call is NOT detected: rotating a page is the R239 family, not compression.

- A pypdf / PyPDF2 PdfWriter + update_page_form_field_values call is NOT detected: filling a form is the R240 family, not compression.

- A pypdf / PyPDF2 PdfReader + merge_page call is NOT detected: merging a page is the R241 watermarking route, not compression.

- A PyMuPDF opener + show_pdf_page call is NOT detected: overlaying a page is the R241 watermarking route, not compression.

- A PyMuPDF opener + rotated insert_text / insert_textbox call is NOT detected: inserting rotated text is the R241 watermarking route, not compression.

- A PyMuPDF opener + add_redact_annot call is NOT detected: annotating text for redaction is the R242 family, not compression.

- A pyhanko sign_pdf / endesive.pdf.cms.sign call is NOT detected: signing a PDF is the R231 e-signature family, not compression.

- A pypdf / PyPDF2 PdfReader call is NOT detected: reading a PDF is not compressing it.

- PDF generation (reportlab Canvas + save, fpdf output, WeasyPrint write_pdf, openpyxl Workbook + save, and the rest of the pdf-generation family's routes) is NOT detected: writing one PDF from content is not compressing an existing PDF.

- PDF merging is NOT detected: combining two or more PDFs into one file is the R236 family, not this one.

- PDF splitting is NOT detected: splitting one PDF into separate files is the R237 family, not this one.

- PDF encryption is NOT detected: password-protecting a PDF is the R238 family, not this one.

- PDF rotation is NOT detected: rotating PDF pages is the R239 family, not this one.

- PDF form filling is NOT detected: entering data into AcroForm fields is the R240 family, not this one.

- PDF watermarking is NOT detected: stamping a watermark onto PDF pages is the R241 family, not this one.

- PDF redaction is NOT detected: removing text from PDF pages is the R242 family, not this one.

- PDF extraction is NOT detected: reading text or field values out of a PDF is the pdf-extraction family, not this one.

- E-signature is NOT detected: applying a cryptographic signature to a PDF is the R231 family, not this one.

- qpdf / Ghostscript / pdfsizeopt subprocess calls are NOT detected: shelling out to an external binary is NOT evidence by design.

- Mindee parse with ANY product is NOT detected: mindee extracts fields from documents; it has no product for the checked operation.

- Azure begin_analyze_document with ANY model id is NOT detected: the call carries an opaque model id, not a typed call for the checked operation.

- Veryfi calls of ANY kind are NOT detected: veryfi extracts fields from documents; it has no method for the checked operation.

- Google Document AI process_document / batch_process_documents with ANY processor is NOT detected: the processor is named by an opaque per-project resource name, and Document AI has no operation for the checked operation.

- Eden AI universal-ai calls with ANY model id are NOT detected: Eden AI documents no model for the checked operation.

- Textract calls of ANY kind are NOT detected: Textract reads documents; it has no operation with a fixed fingerprint for the checked operation.

- LlamaParse calls are NOT detected: its parsing API reads documents; it has no operation for the checked operation.

- Nanonets / Docsumo / ABBYY Vantage / Rossum / Klippa / Parseur / Extend calls are NOT detected: opaque model / skill / queue / template / workflow IDs, or a generic upload endpoint with the document type configured outside the call — all extraction-side, no fixed fingerprint.

- A hand-rolled compression built on raw PDF dictionary editing (writing content streams by hand with no listed call) is NOT detected: the tool requires a listed call.

- A detected compression does not prove the file got smaller: the tool detects the compression call, not the output size.

- PDF extraction claims ("extract pdf", "pdf extraction"), PDF generation claims ("generate pdf", "pdf generation"), PDF merging claims ("merge pdf", "pdf merging"), PDF splitting claims ("split pdf", "pdf splitting"), PDF encryption claims ("encrypt pdf", "pdf encryption"), PDF rotation claims ("rotate pdf", "pdf rotation"), PDF form filling claims ("fill pdf form", "pdf form filling"), PDF watermarking claims ("add watermark to pdf", "pdf watermarking"), PDF redaction claims ("redact pdf", "pdf redaction"), spreadsheet reading claims ("read spreadsheet", "spreadsheet reading"), spreadsheet generation claims ("generate spreadsheet", "spreadsheet generation"), Word document reading claims ("read word document", "word document reading"), Word document generation claims ("generate word document", "word document generation"), presentation reading claims ("read presentation", "presentation reading"), presentation generation claims ("generate presentation", "presentation generation"), table extraction claims ("extract tables", "table extraction"), invoice extraction claims ("extract invoices", "invoice extraction"), receipt extraction claims ("extract receipts", "receipt extraction"), ID document extraction claims ("extract passports", "passport extraction"), bank check extraction claims ("extract bank checks", "check extraction"), bank statement extraction claims ("extract bank statements", "statement extraction"), tax form extraction claims ("extract tax forms", "extract w2 forms", "1099 extraction"), pay stub extraction claims ("extract pay stubs", "payslip extraction"), health insurance card extraction claims ("extract health insurance cards", "health insurance card extraction"), business card extraction claims ("extract business cards", "business card extraction"), credit card extraction claims ("extract credit cards", "credit card extraction"), contract extraction claims ("extract contracts", "contract extraction"), mortgage extraction claims ("extract mortgages", "mortgage extraction"), resume extraction claims ("extract resumes", "resume extraction"), bill of lading extraction claims ("extract bills of lading", "bill of lading extraction"), delivery note extraction claims ("extract delivery notes", "delivery note extraction"), carte grise extraction claims ("extract carte grises", "carte grise extraction"), energy bill extraction claims ("extract energy bills", "energy bill extraction"), marriage certificate extraction claims ("extract marriage certificates", "marriage certificate extraction"), bank account details extraction claims ("extract bank account details", "bank account details extraction"), nutrition facts label extraction claims ("extract nutrition facts labels", "nutrition facts label extraction"), material certificate extraction claims ("extract material certificates", "material certificate extraction"), US mail extraction claims ("extract us mail", "us mail extraction"), invoice splitter claims ("split invoices", "invoice splitting"), multi-receipts detection claims ("detect multiple receipts", "multi receipt detection"), French health card extraction claims ("extract carte vitales", "french health card extraction"), Indian passport extraction claims ("extract indian passports", "indian passport extraction"), driver license extraction claims ("extract driver licenses", "driver license extraction"), vaccination card extraction claims ("extract vaccination cards", "vaccination card extraction"), document cropping claims ("crop documents", "document cropping"), image rotation claims ("rotate image", "image rotation"), e-signature claims ("signs documents", "electronic signature"), payment processing claims ("process payments", "payment processing"), and OCR claims ("recognize text in images", "optical character recognition") are NOT in the phrase lists: this family covers the checked operation only.

- As with every family: static pattern matching, not semantic judgement; dead code counts; alias chains the tracer cannot follow are missed; exact phrases only, not semantics; denial handling depends on the denial phrase list; each route must sit in a single module.
