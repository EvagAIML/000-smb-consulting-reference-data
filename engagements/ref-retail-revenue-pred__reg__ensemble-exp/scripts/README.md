# scripts/

One-shot Python utilities tied to this engagement's deliverable.

## pass2_rewrite.py

Single-pass Pass-2 narrative rewrite of `notebooks/hill_country_grocer__reg__ensemble.ipynb`:

- replaces every body markdown cell against the v2.2 canon (Process / Outcome and Process / Analysis / Outcome patterns);
- collapses the four-cell top-of-notebook block into the v2.2 three-cell structure (Title / Combined VP+ES+ProblemSpace+Live-Deployment / Code Execution divider);
- adds the deployment section (Hugging Face Space asset writers) between Model Serialization and the Expanded Executive Summary;
- preserves all 24 originally-executed code cells verbatim (source + outputs + execution_count 1..24).

Used when the executed notebook's embedded base64 image outputs push the file past the harness's `Read` / `NotebookEdit` token budget, which makes the canonical in-tool edit path unavailable. Run once from any cwd:

    python3 engagements/ref-retail-revenue-pred__reg__ensemble-exp/scripts/pass2_rewrite.py

Post-conditions verified in-script: cell count (60), markdown/code split (33/27), code-cell execution-count preservation (1..24 on the 24 original code cells; None on the 3 new deployment code cells), absence of self-characterizing voice terms in markdown cell prose, and presence of both locked HF Space names in the combined-top cell.

This is a one-shot artifact. The rewrite has already landed in the notebook; the script is retained alongside the deliverable as reproducibility evidence rather than as a re-runnable workflow.
