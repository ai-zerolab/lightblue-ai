import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from pydantic_ai import BinaryContent

from lightblue_ai.tools.local.command import BashTool
from lightblue_ai.tools.local.files import (
    EditTool,
    GlobTool,
    GrepTool,
    ListTool,
    ReplaceTool,
    ViewTool,
    _get_file_info,
)


class TestGlobTool:
    @pytest.fixture
    def glob_tool(self):
        return GlobTool()

    @pytest.mark.asyncio
    async def test_glob_pattern_matching(self, glob_tool, tmp_path):
        # Create test files in tmp_path with different modification times
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file3 = tmp_path / "file3.py"

        # Create the files
        file1.touch()
        file2.touch()
        file3.touch()

        # Create a simple function to directly test the sorting logic
        def mock_glob_and_sort():
            # Return the files in the order we want to test
            files = [str(file1), str(file2), str(file3)]

            # Create a dictionary mapping file paths to mock stat objects
            stat_results = {
                str(file1): Mock(st_mtime=100),
                str(file2): Mock(st_mtime=300),  # Newest
                str(file3): Mock(st_mtime=200),
            }

            # Sort the files by modification time (newest first)
            files.sort(key=lambda f: stat_results[f].st_mtime, reverse=True)
            return files

        # Get the expected sorted result
        expected_result = mock_glob_and_sort()

        # Now test the actual call function with mocks
        with patch("pathlib.Path.glob") as mock_glob:
            # Return the files in any order, the function should sort them
            mock_glob.return_value = [file1, file3, file2]

            # Create a side effect function for Path.stat
            def mock_stat_side_effect(self):
                path_str = str(self)
                if "file1.py" in path_str:
                    return Mock(st_mtime=100)
                elif "file2.py" in path_str:
                    return Mock(st_mtime=300)
                elif "file3.py" in path_str:
                    return Mock(st_mtime=200)
                return Mock(st_mtime=0)

            # Apply the patch to Path.stat
            with patch.object(Path, "stat", mock_stat_side_effect):
                # Test the call function
                result = await glob_tool.call("**/*.py")

            # Verify the glob pattern was passed correctly
            mock_glob.assert_called_once_with("**/*.py")

            # Verify the results are sorted by modification time (newest first)
            assert result == expected_result


class TestGrepTool:
    @pytest.fixture
    def grep_tool(self):
        return GrepTool()

    @pytest.mark.asyncio
    async def test_grep_pattern_matching(self, grep_tool, tmp_path):
        # Create a test file path
        test_file = tmp_path / "test_file.txt"

        # Mock file content
        mock_file_content = [
            "line 1: some text\n",
            "line 2: important info\n",
            "line 3: more text\n",
            "line 4: important data\n",
            "line 5: final line\n",
        ]

        with (
            patch("pathlib.Path.glob") as mock_glob,
            patch("pathlib.Path.is_dir", return_value=False),
            patch("pathlib.Path.stat") as mock_stat,
            patch("pathlib.Path.open") as mock_open,
        ):
            mock_glob.return_value = [test_file]
            mock_stat.return_value = Mock(st_mtime=100)

            # Mock file open and reading
            mock_file = MagicMock()
            mock_file.readlines.return_value = mock_file_content
            mock_open.return_value.__enter__.return_value = mock_file

            # Test the call function with a pattern that matches lines with "important"
            result = await grep_tool.call(pattern="important", include="**/*.txt", context_lines=1)

            # Verify the glob pattern was passed correctly
            mock_glob.assert_called_once_with("**/*.txt")

            # Verify the results contain the expected matches with context
            assert len(result) == 2  # Two matches for "important"

            # Check first match
            assert result[0]["file_path"] == str(test_file)
            assert result[0]["line_number"] == 2
            assert result[0]["matching_line"] == "line 2: important info"
            assert len(result[0]["context"]) == 3  # line 1, 2, 3
            assert result[0]["context_start_line"] == 1

            # Check second match
            assert result[1]["file_path"] == str(test_file)
            assert result[1]["line_number"] == 4
            assert result[1]["matching_line"] == "line 4: important data"
            assert len(result[1]["context"]) == 3  # line 3, 4, 5
            assert result[1]["context_start_line"] == 3


class TestListTool:
    @pytest.fixture
    def list_tool(self):
        return ListTool()

    @pytest.mark.asyncio
    async def test_list_directory_contents(self, list_tool, tmp_path):
        # Create test directory structure
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        # Create test files
        (test_dir / "file1.txt").touch()
        (test_dir / "file2.py").touch()
        (test_dir / ".hidden_file").touch()

        # Create subdirectory
        subdir = test_dir / "subdir"
        subdir.mkdir()

        with (
            patch("pathlib.Path.expanduser", return_value=test_dir),
            patch("lightblue_ai.tools.local.files._get_file_info") as mock_get_file_info,
        ):
            # Mock _get_file_info to return predictable results
            def mock_file_info(path):
                return {
                    "name": path.name,
                    "path": str(path),
                    "type": "directory" if path.name == "subdir" else "file",
                    "depth": 0,
                }

            mock_get_file_info.side_effect = mock_file_info

            # Test the call function with non-recursive listing
            result = await list_tool.call(path=str(test_dir), recursive=False)

            # Verify the results
            assert result["path"] == str(test_dir)
            assert result["success"] is True
            assert len(result["entries"]) == 3  # Excluding hidden file

            # Test with include_hidden=True
            result = await list_tool.call(path=str(test_dir), include_hidden=True)

            # Verify the results include hidden files
            assert len(result["entries"]) == 4  # Including hidden file


T = TypeVar("T")


@dataclass
class DummyCtx[T]:
    deps: T


class TestViewTool:
    @pytest.fixture
    def view_tool(self):
        return ViewTool()

    @pytest.mark.asyncio
    async def test_view_text_file(self, view_tool, tmp_path):
        # Create a test file with content
        test_file = tmp_path / "test_file.txt"
        mock_file_content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n"
        test_file.write_text(mock_file_content)

        # Test the call function with a real file
        result = await view_tool.call(file_path=str(test_file))

        # Verify the result is the file content
        assert result == mock_file_content

    @pytest.mark.asyncio
    async def test_view_binary_file(self, view_tool, tmp_path):
        # Create a test binary file
        test_file = tmp_path / "test_image.png"
        mock_binary_content = b"binary content"
        test_file.write_bytes(mock_binary_content)

        # Test the call function with a real binary file
        result = await view_tool.call(file_path=str(test_file))
        # Verify the result is a BinaryContent object
        assert isinstance(result, BinaryContent)
        assert result.data == mock_binary_content
        assert result.media_type == "image/png"


class TestEditTool:
    @pytest.fixture
    def edit_tool(self):
        return EditTool()

    @pytest.mark.asyncio
    async def test_edit_existing_file(self, edit_tool, tmp_path):
        # Create a test file path
        test_file = tmp_path / "test_file.txt"
        mock_file_content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n"

        with (
            patch("pathlib.Path.expanduser", return_value=test_file),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_dir", return_value=False),
            patch("pathlib.Path.open") as mock_open,
        ):
            # Mock file open and reading/writing
            mock_file = MagicMock()
            mock_file.read.return_value = mock_file_content
            mock_open.return_value.__enter__.return_value = mock_file

            # Test the call function
            result = await edit_tool.call(
                file_path=str(test_file),
                old_string="Line 3\n",
                new_string="Modified Line 3\n",
            )

            # Verify the result is a success message
            assert "Successfully edited file" in result

            # Verify the write operation was called with the modified content
            expected_content = "Line 1\nLine 2\nModified Line 3\nLine 4\nLine 5\n"
            mock_file.write.assert_called_once_with(expected_content)

    @pytest.mark.asyncio
    async def test_create_new_file(self, edit_tool, tmp_path):
        # Create a test file path
        test_file = tmp_path / "new_file.txt"

        with (
            patch("pathlib.Path.expanduser", return_value=test_file),
            patch("pathlib.Path.parent") as mock_parent,
            patch("pathlib.Path.open") as mock_open,
        ):
            # Mock parent directory
            mock_parent.exists.return_value = True

            # Mock file open and writing
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            # Test the call function for creating a new file
            result = await edit_tool.call(file_path=str(test_file), old_string="", new_string="New file content")

            # Verify the result is a success message
            assert "Successfully created new file" in result

            # Verify the write operation was called with the new content
            mock_file.write.assert_called_once_with("New file content")


class TestReplaceTool:
    @pytest.fixture
    def replace_tool(self):
        return ReplaceTool()

    @pytest.mark.asyncio
    async def test_replace_file(self, replace_tool, tmp_path):
        # Create a test file path
        test_file = tmp_path / "test_file.txt"

        with (
            patch("pathlib.Path.expanduser", return_value=test_file),
            patch("pathlib.Path.parent") as mock_parent,
            patch("pathlib.Path.open") as mock_open,
        ):
            # Mock parent directory
            mock_parent.exists.return_value = True

            # Mock file open and writing
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            # Test the call function
            result = await replace_tool.call(file_path=str(test_file), content="New file content")

            # Verify the result is a success message
            assert "Successfully wrote to file" in result

            # Verify the write operation was called with the new content
            mock_file.write.assert_called_once_with("New file content")


class MockProcess:
    def __init__(self, stdout=b"", stderr=b"", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.communicate = AsyncMock(return_value=(stdout, stderr))
        self.kill = MagicMock()


class TestBashTool:
    @pytest.fixture
    def bash_tool(self):
        return BashTool()

    @pytest.mark.asyncio
    async def test_bash_command_execution(self, bash_tool):
        # Mock asyncio.create_subprocess_exec
        mock_process = MockProcess(stdout=b"stdout output", stderr=b"stderr output", returncode=0)
        with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
            # Test the call function
            result = await bash_tool.call(command=["echo", "hello"], timeout_seconds=10)

            # Verify the command was executed correctly
            mock_exec.assert_called_once()
            args, kwargs = mock_exec.call_args
            assert args == ("echo", "hello")

            # Verify the result contains the expected output
            assert result["stdout"] == "stdout output"
            assert result["stderr"] == "stderr output"
            assert result["return_code"] == 0

    @pytest.mark.asyncio
    async def test_bash_timeout(self, bash_tool):
        # Mock asyncio.create_subprocess_exec
        mock_process = MockProcess()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
            # Test the call function with a timeout
            result = await bash_tool.call(command=["sleep", "100"], timeout_seconds=1)

            # Verify the command was executed
            mock_exec.assert_called_once()

            # Verify the result indicates a timeout
            assert "timed out" in result.get("error", "")
            assert result["return_code"] == 124


def test_get_file_info(tmp_path):
    # Create a test file
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("Test content")

    # Create a test directory
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    # Test the _get_file_info function for a file
    file_info = _get_file_info(test_file)

    # Verify the result contains the expected file information
    assert file_info["name"] == "test_file.txt"
    assert file_info["path"] == str(test_file)
    assert file_info["type"] == "file"
    assert "size" in file_info
    assert "modified" in file_info

    # Test the _get_file_info function for a directory
    dir_info = _get_file_info(test_dir)

    # Verify the result contains the expected directory information
    assert dir_info["name"] == "test_dir"
    assert dir_info["path"] == str(test_dir)
    assert dir_info["type"] == "directory"
