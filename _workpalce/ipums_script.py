from pathlib import Path
import pandas as pd

from ipumspy import readers


def main():
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    csv_path = output_dir / "usa_00002.csv"
    result_path = output_dir / "children_noncitizen_parents.csv"

    xml_file = Path("data")  / "usa_00001.xml"
    dat_file = Path("data") / "usa_00001.dat.gz"

    ddi = readers.read_ipums_ddi(str(xml_file))
    df = readers.read_microdata(ddi, str(dat_file))
    df.to_csv(csv_path, index=False)

    # 1-keep children under age 1 who were born in the U.S.
    children = df[(df["AGE"] < 1) & (df["BPL"].between(1, 56))].copy()

    # 2-valid data point - children with both mother and father links
    children = children[(children["MOMLOC"].notna()) & (children["POPLOC"].notna())].copy()

    # 3-find parent citizenship from the same household
    parent_citizenship = df[["SERIAL", "PERNUM", "CITIZEN"]].rename(
        columns={"PERNUM": "MOMLOC", "CITIZEN": "mother_citizen"}
    )
    ## find mom 
    children = children.merge(parent_citizenship, on=["SERIAL", "MOMLOC"], how="left")
    ## find dad 
    parent_citizenship = df[["SERIAL", "PERNUM", "CITIZEN"]].rename(
        columns={"PERNUM": "POPLOC", "CITIZEN": "father_citizen"}
    )
    children = children.merge(parent_citizenship, on=["SERIAL", "POPLOC"], how="left")

    # 4-identify when both parents are non-citizens
    match = children[(children["mother_citizen"] == 0) & (children["father_citizen"] == 0)]

    # Save result
    match.to_csv(result_path, index=False)
    print(f"Saved matching children to {result_path}")
    print(f"Number of matching rows: {len(match)}")
    print(match[["SERIAL", "PERNUM", "AGE", "BPL", "mother_citizen", "father_citizen"]].head())


if __name__ == "__main__":
    main()
