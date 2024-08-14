```mermaid
flowchart TD
	node1["convert_markdown_to_html@0"]
	node2["convert_markdown_to_pdf@0"]
	node3["convert_markdown_to_pptx@0"]
	node4["convert_pptx_to_pdf@0"]
	node5["generate_scenario@0"]
	node3-->node4
	node5-->node1
	node5-->node2
	node5-->node3
```
