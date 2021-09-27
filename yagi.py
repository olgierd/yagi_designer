#!/usr/bin/python3

import argparse
import shutil
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QDoubleSpinBox, QLabel

wire_template = "GW ###WNR 15 ###POS###WNR -###LEN###WNR 0.0 ###POS###WNR ###LEN###WNR 0.0 ###EL_R"

tpl = """GE 0 0 0.0 0.0 0.0 0.0 0.0 0.0 0.0
EX 0 2 8 0 1.0 0.0 0.0 0.0 0.0 0.0
FR 0 3 0 0 ###FREQ 1.0 ###FREQ 0.0 0.0 0.0
NH 0 0 0 0 0.0 0.0 0.0 0.0 0.0 0.0
NE 0 10 1 10 -1.35 0.0 -1.35 0.3 0.0 0.3
RP 0 19 37 1000 0.0 0.0 10.0 10.0 0.0 0.0
EN 0 0 0 0 0.0 0.0 0.0 0.0 0.0 0.0
"""


class YagiDesign(QWidget):
    def parse_output(self, output_file):
        with open(output_file) as f:
            f = f.read().splitlines()

        q = 0

        while "INPUT PARAMETERS" not in f[q]:
            q = q+1

        q += 3
        real, imag = [float(x) for x in f[q].split(' ') if x][6:8]

        while "RADIATION PATTERNS" not in f[q]:
            q = q+1

        q += 14
        fwd_gain = float([x for x in f[q].split(' ') if x][4])

        q += 342
        rew_gain = float([x for x in f[q].split(' ') if x][4])

        zl = complex(real, imag)
        z0 = 50
        mag_gamma = abs((zl-z0)/(zl+z0))
        vswr = (1+mag_gamma)/(1-mag_gamma)

        results = {"Re": real, "Im": imag, "dBi": fwd_gain, "SWR": vswr, "F/B": fwd_gain-rew_gain}
        return results

    def prepare_template(self, elements):
        template = ""
        for x in range(1, elements+1):
            template += wire_template.replace("###WNR", str(x)) + "\n"
        template += tpl

        return template

    def __init__(self, args):
        super(QWidget, self).__init__()
        layout = QVBoxLayout()

        self.filepath = "/tmp/yagidesign"

        self.elements = int(args.elements)
        self.template = self.prepare_template(self.elements)
        self.spinners = {}

        el_names = ["Ref", "DE"] + [f"D{x+1}" for x in range(self.elements)]

        hl = QHBoxLayout()
        el_d_sb = QDoubleSpinBox()
        el_d_sb.setMinimum(0.1)
        el_d_sb.setMaximum(20)
        el_d_sb.setSingleStep(0.1)
        el_d_sb.setValue(3.2)
        self.spinners["EL_D"] = el_d_sb
        hl.addWidget(QLabel("Element diameter (mm)"))
        hl.addWidget(el_d_sb)
        layout.addLayout(hl)

        for x in range(self.elements):
            hl = QHBoxLayout()

            pos_sb = QDoubleSpinBox()
            pos_sb.setMinimum(0)
            pos_sb.setMaximum(1000)
            pos_sb.setSingleStep(0.1)   # 1mm resolution

            len_sb = QDoubleSpinBox()
            len_sb.setMinimum(1)
            len_sb.setMaximum(1000)
            len_sb.setSingleStep(0.1)

            len_sb.setValue(100)
            pos_sb.setValue(x*10)

            self.spinners[f"POS{x+1}"] = pos_sb
            self.spinners[f"LEN{x+1}"] = len_sb

            hl.addWidget(QLabel(el_names[x] + " pos/len (cm)"))
            hl.addWidget(pos_sb)
            hl.addWidget(len_sb)

            layout.addLayout(hl)

        hl = QHBoxLayout()
        freq_sb = QDoubleSpinBox()
        freq_sb.setMinimum(0.1)
        freq_sb.setMaximum(1500)
        freq_sb.setSingleStep(0.1)
        freq_sb.setValue(145)
        self.spinners["FREQ"] = freq_sb
        hl.addWidget(QLabel("Frequency"))
        hl.addWidget(freq_sb)
        layout.addLayout(hl)

        for _, sb in self.spinners.items():
            sb.valueChanged.connect(self.update)

        output_labels = ["Re", "Im", "Gain dBi", "Gain dBd", "SWR", "F/B"]

        self.outputs = {}

        for ol in output_labels:
            hl = QHBoxLayout()

            out = QLabel(".")
            self.outputs[ol] = out

            hl.addWidget(QLabel(ol + ":"))
            hl.addWidget(out)

            layout.addLayout(hl)

        self.setLayout(layout)

    def update(self):

        cc = self.template

        # set element radius (dia/2)
        el_d = self.spinners["EL_D"].value()
        cc = cc.replace("###EL_R", f"{el_d/1000/2:.5}")

        # set element positions in the template
        for x in range(0, self.elements):
            position = self.spinners[f"POS{x+1}"].value()
            cc = cc.replace(f"###POS{x+1}", f"{position/100:.5}")

        # set element lengths
        for x in range(0, self.elements):
            el_len = self.spinners[f"LEN{x+1}"].value()
            cc = cc.replace(f"###LEN{x+1}", f"{el_len/2/100:.5}")

        freq = self.spinners["FREQ"].value()
        cc = cc.replace("###FREQ", f"{freq:.5}")

        if args.verbose:
            print(cc)

        with open(self.filepath + ".nec", 'w') as f:
            f.write(cc)

        subprocess.run(["nec2c", "-i", self.filepath + ".nec"])

        parameters = self.parse_output(self.filepath + ".out")

        self.outputs["Re"].setText(f"{parameters['Re']:5.3}")
        self.outputs["Im"].setText(f"{parameters['Im']:5.3}")
        self.outputs["Gain dBi"].setText(f"{parameters['dBi']:5.3}")
        self.outputs["Gain dBd"].setText(f"{parameters['dBi']-2.15:5.3}")
        self.outputs["SWR"].setText(f"{parameters['SWR']:5.3}")
        self.outputs["F/B"].setText(f"{parameters['F/B']:5.3}")


parser = argparse.ArgumentParser(description="Simple QT5 nec2c wrapper for designing Yagis. Made by SQ3SWF 2021")
parser.add_argument("-e", "--elements", help="Total number of antenna elements", type=int, required=True)
parser.add_argument("-v", "--verbose", help="Print debug info", type=bool)
args = parser.parse_args()


def main():
    if not shutil.which("nec2c"):
        print("nec2c binary not found in PATH. Please install nec2c package.")

    app = QApplication(["SWF Yagi designer"])
    yd = YagiDesign(args)
    yd.show()
    app.exec_()


if __name__ == '__main__':
    main()
