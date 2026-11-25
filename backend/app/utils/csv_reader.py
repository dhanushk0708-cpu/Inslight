import io
import pandas as pd


def read_csv_safe(source, is_bytes: bool = False) -> pd.DataFrame:
    """
    Try multiple encodings to read CSV.
    Handles Excel exports (cp1252), Latin-1, UTF-8-BOM, etc.
    """
    encodings = ["utf-8", "utf-8-sig", "cp1252", "latin-1", "iso-8859-1", "ascii"]

    for enc in encodings:
        try:
            if is_bytes:
                df = pd.read_csv(io.BytesIO(source), encoding=enc)
            else:
                df = pd.read_csv(source, encoding=enc)
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            # Re-raise non-encoding error
            raise e

    # Last resort: latin-1 with error replacement
    if is_bytes:
        return pd.read_csv(io.BytesIO(source), encoding="latin-1", on_bad_lines="skip")
    else:
        return pd.read_csv(source, encoding="latin-1", on_bad_lines="skip")
