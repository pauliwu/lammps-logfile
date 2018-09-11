import numpy as np
import pandas as pd
from io import BytesIO, StringIO

class File:
    def __init__(self, ifile):
        # Identifiers for places in the log file
        self.start_thermo_strings = ["Memory usage per processor", "Per MPI rank memory allocation"]
        self.stop_thermo_strings = ["Loop time"]
        self.data_dict = {}
        self.headers = []
        self.output_before_first_run = ""
        self.partial_logs = []
        if hasattr(ifile, "read"):
            self.logfile = ifile
        else:
            self.logfile = open(ifile, 'r')
        self.read_file_to_dict()

    def read_file_to_dict(self):
        contents = self.logfile.readlines()
        header_flag = False
        before_first_run_flag = True
        i = 0
        while i < len(contents):
            line = contents[i]
            if before_first_run_flag:
                self.output_before_first_run += line

            if header_flag:
                headers = line.split()
                tmpString = ""
                # Check wheter any of the thermo stop strigs are in the present line
                while not sum([string in line for string in self.stop_thermo_strings]) >= 1:
                    if "\n" in line:
                        tmpString+=line
                    i+=1
                    if i<len(contents):
                        line = contents[i]
                    else:
                        break
                partialLogContents = pd.read_table(StringIO(tmpString), sep=r'\s+')

                if (self.headers != headers):
                    # If the log header changes, i.e. the thermo data to be outputted chages,
                    # we flush all prevous log data. This is a limitation of this implementation. 
                    self.flush_dict_and_set_new_header(headers)

                self.partial_dict = {}
                for name in headers:
                    self.data_dict[name] = np.append(self.data_dict[name],partialLogContents[name])
                    self.partial_dict[name] = np.append(np.asarray([]), partialLogContents[name])
                self.partial_logs.append(self.partial_dict)
                header_flag = False

            # Check whether the string matches any of the start string identifiers
            if sum([line.startswith(string) for string in self.start_thermo_strings]) >= 1:
                header_flag = True
                before_first_run_flag = False
            i += 1

    def flush_dict_and_set_new_header(self, headers):
        self.data_dict = {}
        for entry in headers:
            self.data_dict[entry] = np.asarray([])
        self.headers = headers


    def get(self, entry_name, run_num=-1):
        if run_num == -1:
            if entry_name in self.data_dict.keys():
                return self.data_dict[entry_name]
            else:
                return None
        else:
            if len(self.partial_logs) > run_num:
                partial_log = self.partial_logs[run_num]
                if entry_name in partial_log.keys():
                    return partial_log[entry_name]
                else:
                    return None
            else:
                return None

    def get_num_partial_logs(self):
        return len(self.partial_logs)