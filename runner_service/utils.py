

class RunnerServiceError(Exception):
    pass


def fread(file_path):
    """ return the contents of the given file """
    with open(file_path, 'r') as file_fd:
        return file_fd.read().strip()
