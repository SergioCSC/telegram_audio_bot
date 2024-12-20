from markitdown import MarkItDown

import tempfile

def mark_it_down(file_bytes: bytes, file_ext: str) -> str:
    md = MarkItDown()
    with tempfile.NamedTemporaryFile(mode='wb', suffix=file_ext,
            delete_on_close=False) as temp_file:
        temp_file.write(file_bytes)
        temp_file.close()
        result = md.convert(temp_file.name)
    return result.text_content