import os

def read_file(file_path):
    try:
        with open(file_path, 'r', encoding="utf-8", errors="ignore") as file:
            return file.read()
    except Exception as e:
        return f"Error reading {file_path}: {e}"


class ProjectReader:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        if not os.path.isdir(self.folder_path):
            raise ValueError(f"The path {self.folder_path} is not a valid directory.")

    def list_files(self, recursive=True):
        if recursive:
            return [
                os.path.join(root, file)
                for root, _, files in os.walk(self.folder_path)
                if '/venv/' not in root.replace('\\', '/')
                for file in files
                if file.endswith('.py') and not file.startswith('._')
            ]
        else:
            return [
                os.path.join(self.folder_path, file)
                for file in os.listdir(self.folder_path)
                if file.endswith('.py') and os.path.isfile(os.path.join(self.folder_path, file))
            ]
