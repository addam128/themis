import re

TIMESTAMP = re.compile(r"\s*\d{1,10}\sms(.+)\n")

def filter_file(filename: str, outfile: str):
    with open(filename, "r") as file:
        with open(outfile, "w") as ofile:
            for line in file:
                mat = TIMESTAMP.match(line)
                if mat is not None:
                    ofile.write(mat.group(1))
                    ofile.write("\n")


