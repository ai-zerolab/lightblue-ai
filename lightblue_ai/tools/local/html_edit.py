from pathlib import Path
from typing import Annotated

from lxml import etree, html
from pydantic import Field

from lightblue_ai.tools.base import LightBlueTool, Scope
from lightblue_ai.tools.extensions import hookimpl


class HtmlEditTool(LightBlueTool):
    def __init__(self):
        self.name = "html_edit"
        self.scopes = [Scope.write]
        self.description = """This is a specialized tool for editing HTML files using XPath expressions to target specific elements.

Before using this tool:

1. Use the View tool to understand the HTML file's structure.
2. Verify that the file is a valid HTML document.

This tool allows you to replace the content of HTML elements by:
- Targeting elements with XPath expressions
- Replacing their entire content with new HTML

To make an HTML edit, provide:
1. file_path: The absolute path to the HTML file to modify (must be absolute, not relative).
2. xpath: The XPath expression that identifies the element(s) to modify.
   For example: "//div[@id='header']", "//h1[1]", or "//section[@class='about']".
3. new_content: The new HTML content to replace the inner content of the targeted element(s).
4. match_index: (Optional) The index of the element to modify if multiple elements match the XPath (0-based, default: 0).

Common XPath expressions:
- "//tagname": Selects all elements with the given tag name
- "//tagname[@attr='value']": Selects elements with a specific attribute value
- "//tagname[contains(@attr, 'partial')]": Selects elements with attribute containing a string
- "//tagname[1]": Selects the first element with the given tag name
- "//div[@id='main']//p": Selects all paragraphs inside the div with id="main"
- "//h1 | //h2": Selects all h1 and h2 elements

Examples:
- To replace the main heading and subtitle: xpath="//header", new_content="<h1>New Heading</h1><p>New subtitle text</p>"
- To replace the about section content: xpath="//section[@id='about']", new_content="<h2>About Us</h2><p>New about text...</p>"
- To replace a specific navigation item: xpath="//nav//li[3]", new_content="<li><a href='contact.html'>Contact Us</a></li>"

Best Practices:
- This tool works best for replacing entire chunks of HTML rather than making small edits
- Make comprehensive changes in a single operation instead of multiple small edits
- Use highly specific XPath queries to ensure you target the exact element you want to modify
- Test your XPath queries first to make sure they match exactly what you intend to replace
- Create complete, well-formed HTML fragments for your replacement content
"""

    async def call(  # noqa: C901
        self,
        file_path: Annotated[str, Field(description="Absolute path to the HTML file to edit")],
        xpath: Annotated[str, Field(description="XPath expression to target elements")],
        new_content: Annotated[str, Field(description="New HTML content to replace the targeted elements")],
        match_index: Annotated[
            int | None,
            Field(
                default=None,
                description="Index of the element to modify if multiple elements match the XPath (0-based)",
            ),
        ] = None,
    ) -> str:
        path = Path(file_path).expanduser()

        # Check if file exists
        if not path.exists():
            return f"Error: File not found: {file_path}"

        if path.is_dir():
            return f"Error: Path is a directory, not a file: {file_path}"

        # Read and parse the HTML file
        with path.open("r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        try:
            parser = html.HTMLParser(remove_blank_text=True)
            document = html.fromstring(content, parser=parser)
        except Exception as e:
            return f"Error parsing HTML: {e!s}. Check if the file is a valid HTML document."

        # Find matching elements
        try:
            matching_elements = document.xpath(xpath)
        except Exception as e:
            return f"Error in XPath expression: {e!s}"

        # Check if any elements matched
        if not matching_elements:
            return f"Error: No elements matched the XPath: '{xpath}'"

        # Handle match_index
        if match_index is not None:
            if match_index < 0 or match_index >= len(matching_elements):
                return f"Error: match_index {match_index} is out of range (0-{len(matching_elements) - 1})"
            matching_elements = [matching_elements[match_index]]

        # Apply the replace_content operation to each matching element
        try:
            modified_count = 0

            for element in matching_elements:
                if self._replace_content(element, new_content):
                    modified_count += 1

            # Check if any elements were modified
            if modified_count == 0:
                return "Error: Operation had no effect on the matched elements"

            # Write the modified document back to the file
            new_html_content = html.tostring(document, encoding="utf-8", method="html", pretty_print=True).decode(
                "utf-8"
            )
            with path.open("w", encoding="utf-8") as f:
                f.write(new_html_content)

            element_description = "element" if modified_count == 1 else "elements"

        except Exception as e:
            return f"Error editing HTML file: {e!s}"
        else:
            return f"Successfully modified {modified_count} {element_description} in {file_path}"

    def _replace_content(self, element: etree._Element, new_content: str) -> bool:
        """Replace the content of an element with new HTML content.

        Args:
            element: The element to modify
            new_content: The new HTML content

        Returns:
            Whether the element was modified
        """
        try:
            # Keep the element but remove its current contents
            # Remove all children
            for child in list(element):
                element.remove(child)

            # Clear text content
            element.text = None

            # Check if the new content is HTML or just plain text
            if new_content and (new_content.strip().startswith("<") and new_content.strip().endswith(">")):
                # Parse new content as HTML
                try:
                    new_elements = html.fragments_fromstring(new_content)
                    # Add the new elements as children
                    for new_element in new_elements:
                        element.append(new_element)
                except Exception:
                    # If parsing as HTML fails, use as text
                    element.text = new_content
            else:
                # Use as plain text
                element.text = new_content

            return True

        except Exception:
            # If operation fails, return False
            return False


@hookimpl
def register(manager):
    manager.register(HtmlEditTool())
