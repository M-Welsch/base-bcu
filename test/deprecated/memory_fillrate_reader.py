from subprocess import run, Popen, PIPE, STDOUT, call
from time import sleep


def run_external_command_as_generator(command):
    p = Popen(command, bufsize=0, universal_newlines=True, stdout=PIPE, stderr=STDOUT)
    return p.stdout


class MemoryFillrateReader:
    def readout_memory_fill_level(self):
        out = run_external_command_as_generator(["df", "--output=avail", "/media/BackupHDD"])
        return self.remove_heading_from_df_output(out)

    def remove_heading_from_df_output(self, df_output):
        df_output_cleaned = ""
        for line in df_output:
            if not line.strip() == "Avail":
                df_output_cleaned = int(line.strip())
        return int(df_output_cleaned)


def print_memory_fill_rate(MFR):
    try:
        old_memory_fill_level = MFR.readout_memory_fill_level()
        while True:
            current_memory_fill = MFR.readout_memory_fill_level()
            difference = current_memory_fill - old_memory_fill_level
            old_memory_fill_level = current_memory_fill
            call("clear", shell=True)
            print(f"Memory Usage Increase:\t{difference}")
            sleep(1)
    except KeyboardInterrupt:
        print("Bye")


if __name__ == "__main__":
    MFR = MemoryFillrateReader()
    print_memory_fill_rate(MFR)
