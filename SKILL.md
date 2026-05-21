---
name: academic-pdf-translation-skill
description: Translate academic PDFs into Chinese with terminology control, OCR detection, text extraction, figure preservation, quality checking, and figure-aware PDF output.
---

# Academic PDF Translation Skill

## Python Interpreter Rules

Use the Python interpreter available in the current environment.

Recommended command order:

1. Try `python`.
2. On Windows, if `python` is unavailable, try `py`.
3. If neither works, ask the user to provide their own Python interpreter path.

Do not hard-code a personal Python path in this skill. On Windows, a user may provide a path such as:

```text
C:\Users\用户名\AppData\Local\Programs\Python\Python312\python.exe
```

## Codex Input Handling

This skill supports uploaded PDF attachments in Codex.

When the user uploads a PDF:

1. Use the uploaded PDF as the input document.
2. Save or copy it into the project root as `input.pdf`.
3. If multiple PDFs are uploaded, ask the user which PDF to process.
4. Default to processing `input.pdf`.

Fallback input filename:

- `test.pdf`

If the uploaded PDF is not directly accessible as a local file, ask the user to place the PDF in the project root or provide an accessible file path.

## Codex Execution Workflow

When this skill is invoked, follow this default workflow:

1. Determine the input PDF.
   - Prefer `input.pdf`.
   - If `input.pdf` does not exist, use `test.pdf`.
   - If neither exists, ask the user to upload or provide a PDF.

2. Inspect the PDF to determine whether it is text-based, scanned, or mixed:

   ```bash
   python scripts/inspect_pdf.py input.pdf
   ```

3. Extract text when the PDF contains usable embedded text:

   ```bash
   python scripts/extract_text.py input.pdf
   ```

4. If the inspection indicates scanned pages, image-only pages, or unusable extracted text, report this to the user before OCR. Do not perform OCR automatically without user confirmation.

5. Split the extracted or OCR text into manageable natural-language blocks:

   ```bash
   python scripts/split_text.py
   ```

6. Build a merge plan before full translation:
   - Clean page headers and footers.
   - Remove download notices, copyright notices, license boilerplate, and journal metadata from body translation.
   - Keep author affiliations, funding, acknowledgments, references, and other end matter out of the main body.
   - Detect sentences broken by PDF page boundaries, figure captions, footers, or affiliations.
   - Merge broken blocks before translation.

7. Generate `output/paper_glossary.csv` before translating the body text.

8. Translate by paragraph or logical block. Keep the source meaning complete and preserve the academic register. Do not translate line by line according to PDF visual line breaks.

9. Handle tables, figure captions, equations, references, and end matter separately from body paragraphs.

10. Perform a quality check after translation. Verify terminology consistency, numbers, units, formulas, figure/table numbering, citations, references, and paragraph completeness.

11. Extract original figures from `input.pdf`:

    ```bash
    python scripts/extract_figures.py input.pdf output/extracted_figures
    ```

12. Generate the final translated PDF with inline figures:

    ```bash
    python scripts/export_pdf.py --translation output/translation_final.md --figures-dir output/extracted_figures --output output/translation_final_inline_figures_final.pdf --report output/figure_mapping_report.md --inline-figures
    ```

13. Produce the default output files listed in Output Requirements.

If `python` is unavailable on Windows, replace `python` in the commands above with `py`. If both are unavailable, use the interpreter path supplied by the user.

## Translation Rules

- Use formal, accurate academic Chinese.
- Do not arbitrarily delete, shorten, expand, or reinterpret source content.
- Do not add information that is not present in the original PDF.
- Preserve all numbers, units, equations, formulas, statistical markers, sample IDs, chemical formulas, experimental group names, figure/table numbers, and citation numbers.
- Preserve or consistently translate labels such as `Figure`, `Table`, and `Eq.`. Once a convention is chosen, use it consistently throughout the document.
- Keep professional terminology consistent across the full translation.
- When an abbreviation first appears, provide the Chinese full name and the English abbreviation when appropriate.
- For later occurrences of the same abbreviation, keep the abbreviation unless the context requires clarification.
- Translate table text while preserving the original row and column structure.
- Do not change table values, units, superscripts, subscripts, significance letters, or statistical notes.
- Translate figure captions while preserving figure numbers, sample names, experimental conditions, and units.
- Use translated Chinese figure captions with the original extracted figures.
- Do not translate equations themselves. Translate only the explanatory text before and after equations.
- References and end matter are usually not translated as body text. Preserve authors, journal names, years, volumes, issues, pages, DOI values, and reference order unless the user explicitly asks otherwise.
- Clean page headers, footers, download information, copyright notices, and license boilerplate before translation.
- Merge sentences interrupted by PDF page breaks, figure captions, or layout artifacts before translation.

Example terminology handling:

Source:

```text
deep eutectic solvent (DES)
```

First translation:

```text
深共熔溶剂（DES）
```

Later occurrences:

```text
DES
```

## Glossary Management Rules

For each PDF, generate `output/paper_glossary.csv`.

`output/paper_glossary.csv` has the highest priority for the current paper.

Do not automatically merge `paper_glossary.csv` into `resources/default_glossary.csv` or `resources/domain_glossary.csv`.

Instead, generate `output/merge_candidates.csv` containing only terms that are likely reusable across future papers and require user confirmation.

Classify each term as one of the following:

- `stable_general_term`
- `domain_reusable_term`
- `paper_specific_term`
- `abbreviation_conflict`
- `uncertain_term`

Only `stable_general_term` and `domain_reusable_term` may be suggested for long-term glossary merging.

Sample names, author-defined abbreviations, one-time experimental group names, and ambiguous abbreviations must not be automatically merged.

For ambiguous abbreviations such as GA, CA, FA, and LA, always determine the meaning from the current-paper context. Preserve the current-paper definition in `paper_glossary.csv` and mark the term as `abbreviation_conflict` when ambiguity exists.

When translating a paper, use glossary priority in this order:

1. `output/paper_glossary.csv`
2. `resources/conflict_terms.csv`
3. `resources/domain_glossary.csv`
4. `resources/default_glossary.csv`

## Figure Extraction Rules

When extracting figures:

1. Extract original embedded figures from `input.pdf` when possible.
2. Save extracted figures under `output/extracted_figures/`.
3. Name images by figure order, such as `figure_1.png`, `figure_2.png`, and `figure_3.png`.
4. If exact figure numbers cannot be determined, number figures by appearance order and state this in `output/figure_mapping_report.md`.
5. Do not redraw figures.
6. Preserve clarity as much as possible.
7. Do not crop figures.
8. Keep composite figures together. For example, keep Fig. 4A-M as one complete figure instead of splitting panels.
9. Use the translated Chinese figure captions already produced during translation.
10. Prefer inserting figures near the first body reference to the figure.
11. If placement cannot be determined reliably, place the figure in a final figure plate section and report the reason.

## PDF Output Rules

The default final PDF is:

```text
output/translation_final_inline_figures_final.pdf
```

PDF generation must follow these rules:

1. Use ReportLab for writing Chinese PDF text.
2. Register an existing Windows Chinese font when running on Windows. Try fonts in this order:
   - `C:\Windows\Fonts\msyh.ttc`
   - `C:\Windows\Fonts\simsun.ttc`
   - `C:\Windows\Fonts\simhei.ttf`
3. Do not use PyMuPDF `insert_text` or `insert_textbox` to write Chinese body text, because this may produce square boxes or missing glyphs.
4. Insert each figure near the first body reference to that figure, such as the first occurrence of `图 1`, `图 2`, or `图 3`.
5. If a figure cannot be located reliably in the body, place it in a final figure plate section and explain the reason in the report.
6. Center figures and keep them proportional.
7. Place one complete Chinese caption below each figure, formatted as `图 X. 中文图注...`.
8. Do not repeat figure captions elsewhere in the PDF.
9. Do not output a full figure plate at the end if all figures were successfully inserted inline.
10. If `CO₂` displays incorrectly in PDF output, normalize it to `CO2`. Never allow it to become `CO` and lose the number `2`.
11. If figure extraction or figure placement fails, report the reason and still preserve the text-only translated output.

## Output Requirements

Default outputs:

1. `output/translation_final.md`
2. `output/paper_glossary.csv`
3. `output/merge_candidates.csv`
4. `output/quality_check_full.md`
5. `output/extracted_figures/`
6. `output/figure_mapping_report.md`
7. `output/inline_figure_report.md`
8. `output/translation_final_inline_figures_final.pdf`

Optional outputs when requested by the user:

- Bilingual Chinese-English DOCX.
- Chinese-only DOCX.
- Chinese-only PDF.
- Bilingual Chinese-English PDF.
- Markdown document.
- Figure-preserving translated PDF.

## Final Report Requirements

After completion, report:

1. Whether the final PDF was generated successfully.
2. Which Chinese font was used for PDF output.
3. How many figures were extracted.
4. Which figures were inserted inline in the body.
5. Whether any figures could not be extracted or located.
6. Whether any terminology conflicts were found.

The final response should clearly list the generated files and mention any known limitations, such as OCR uncertainty, unreadable pages, missing figures, or tables that required manual reconstruction.
