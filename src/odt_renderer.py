import os
import zipfile
import re
import shutil
from jinja2 import Template

class OdtTemplate:
    def __init__(self, template_path):
        self.template_path = template_path

    def render(self, context, output_path):
        """
        Renders the ODT template with the given context and saves to output_path.
        """
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Template not found: {self.template_path}")

        # 1. Copy template to output path (start with a copy)
        shutil.copy(self.template_path, output_path)

        # 2. Read, Clean, Render, Write content.xml
        # We need to operate on the output file now
        try:
            # We use a temporary buffer or read/write logic
            # zipfile doesn't support easy "replace file in place" without copying other files.
            # But since we just copied the whole file to output_path, we can treat output_path as our working zip.
            # Python's zipfile append mode 'a' adds new files, but to replace we usually need to rewrite the zip.
            # Easiest way: Read all, replace content.xml, write all to new zip.
            
            # Strategy:
            # 1. Read 'output_path' into memory (it's a copy of template).
            # 2. Open it for reading.
            # 3. Create a NEW temp zip.
            # 4. Copy all files from 2 to 3, EXCEPT 'content.xml' (and maybe 'styles.xml' if we want to support that too).
            # 5. Process 'content.xml':
            #    a. Clean tags
            #    b. Render Jinja
            # 6. Write processed 'content.xml' to 3.
            # 7. Move 3 to 'output_path'.
            
            temp_output = output_path + ".tmp"
            
            with zipfile.ZipFile(self.template_path, 'r') as source_zip:
                with zipfile.ZipFile(temp_output, 'w') as target_zip:
                    for item in source_zip.infolist():
                        if item.filename == 'content.xml':
                            # Process Content
                            xml_content = source_zip.read(item.filename).decode('utf-8')
                            cleaned_xml = self.clean_xml(xml_content)
                            rendered_xml = self.render_jinja(cleaned_xml, context)
                            target_zip.writestr(item, rendered_xml)
                        else:
                            # Copy others
                            target_zip.writestr(item, source_zip.read(item.filename))
            
            # Replace output with temp
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(temp_output, output_path)

        except Exception as e:
            if os.path.exists(temp_output):
                os.remove(temp_output)
            raise e

    def clean_xml(self, xml_content):
        """
        Removes XML tags occurring inside {{ }} brackets.
        Example: {{<span...>my_var</span>}} -> {{my_var}}
        """
        # Regex to find {{ ... }} blocks, non-greedy
        # We need to handle potential newlines or complex XML? content.xml is usually one long line or formatted.
        
        def replace_tags_in_match(match):
            full_match = match.group(0)
            # Remove all <...> 
            # Note: This is aggressive. If user put actual XML chars in variable names, it breaks.
            # But variable names should be clean.
            cleaned = re.sub(r'<[^>]+>', '', full_match)
            return cleaned

        # Pattern: curly braces with anything in between.
        # We must be careful not to match across multiple variables if they are on same line?
        # {{a}} ... {{b}} -> regex might match {{a}} ... {{b}} as one block if we are not careful.
        # Use ungreedy .*?
        pattern = r'\{\{.*?\}\}'
        return re.sub(pattern, replace_tags_in_match, xml_content, flags=re.DOTALL)

    def render_jinja(self, xml_content, context):
        """
        Renders the cleaned XML string using Jinja2.
        """
        template = Template(xml_content, autoescape=True) 
        # content.xml is XML, so autoescape=True is good practice to escape context values (e.g. < > &)
        return template.render(context)
