# 📘 Guide: Using Evidence in DS Report Section

## 🎯 Purpose
This guide explains how to use the automatically collected evidence artifacts in the final DS (Delivery Summary) report section.

## 📋 Required Evidence for DS Report

### Mandatory References
Your DS report **must** include:

1. **SBOM Acknowledgment**
2. **SCA Results Summary**
3. **Traceability Information**
4. **Compliance Statement**

## 📝 Template Usage

### Quick Start
Use the auto-generated template for each commit:
```bash
# Latest template
cp EVIDENCE/templates/ds-report-latest.md DS_REPORT.md

# Or commit-specific
cp EVIDENCE/templates/ds-report-{commit}.md DS_REPORT.md
