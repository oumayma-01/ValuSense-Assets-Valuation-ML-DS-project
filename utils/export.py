import json
import csv
import io


def result_to_json(result):
    clean = {k: v for k, v in result.items() if not k.startswith("_")}
    return json.dumps(clean, indent=2, default=str)


def result_to_csv_row(result):
    rec = result.get("recommendation") or result
    val = result.get("valuation") or {}
    row = {
        "timestamp": result.get("timestamp", ""),
        "asset_name": result.get("asset_name", ""),
        "recommended_method": rec.get("method", rec.get("recommended_method", "")),
        "confidence": rec.get("confidence", ""),
        "ml_prediction": rec.get("ml_prediction", ""),
        "ifrs_override": rec.get("ifrs_override", ""),
        "valuation_price": result.get("valuation_price", val.get("price") or val.get("fair_value") or ""),
    }
    for k in ["price", "fair_value", "forward_price", "forward_rate", "fair_value_per_share", "error"]:
        if k not in row:
            row[k] = val.get(k, "")
    alts = result.get("alternatives", [])
    for i, alt in enumerate(alts[:3]):
        row[f"alt_{i+1}_method"] = alt.get("method", "")
        row[f"alt_{i+1}_prob"] = alt.get("probability", "")
    return row


def results_to_csv(results):
    output = io.StringIO()
    if not results:
        return output.getvalue()
    rows = [result_to_csv_row(r) for r in results]
    if not rows:
        return output.getvalue()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
