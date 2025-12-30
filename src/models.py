import os
import json
import shutil
from src.utils import CONFIG_DIR, TEMPLATE_DIR, ensure_directories, extract_fields_from_docx

class ProjectManager:
    def __init__(self):
        ensure_directories()
        self.current_project_file = None
        self.project_data = {}

    def get_project_list(self):
        """Returns a list of project display names, respecting the saved order."""
        # 0. SCAN for new folders in Template Directory
        self.scan_for_projects()
        
        # 1. Get files
        files = [f for f in os.listdir(CONFIG_DIR) if f.endswith('.json') and f != 'projects_order.json']
        
        # 2. Get saved order
        order_file = os.path.join(CONFIG_DIR, 'projects_order.json')
        saved_order = []
        if os.path.exists(order_file):
            try:
                with open(order_file, 'r', encoding='utf-8') as f:
                    saved_order = json.load(f)
            except:
                saved_order = []
        
        # 3. Sort
        file_map = {f: f.replace(".json", "").replace("_", " ").title() for f in files}
        
        result_list = []
        
        # Add Ordered items first
        for name_key in saved_order:
             matching_file = None
             for f, display in file_map.items():
                 if display == name_key:
                     matching_file = f
                     break
            
             if matching_file:
                 result_list.append(name_key)
                 del file_map[matching_file] 
        
        # Add remaining
        for f, display in file_map.items():
            result_list.append(display)
            
        return result_list

    def save_project_order(self, order_list):
        order_file = os.path.join(CONFIG_DIR, 'projects_order.json')
        try:
            with open(order_file, 'w', encoding='utf-8') as f:
                json.dump(order_list, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save order: {e}")

    def create_project(self, name):
        safe_name = name.lower().replace(" ", "_").replace("/", "").replace("\\", "")
        filename = safe_name + ".json"
        filepath = os.path.join(CONFIG_DIR, filename)
        
        if os.path.exists(filepath):
            raise FileExistsError(f"Project '{name}' already exists.")
        
        # Directory
        project_template_dir = os.path.join(TEMPLATE_DIR, safe_name)
        os.makedirs(project_template_dir, exist_ok=True)
        
        data = {
            "project_name": name,
            "project_id": safe_name,
            "templates": [],
            "fields": []
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        return filepath

    def load_project(self, display_name):
        filename = display_name.lower().replace(" ", "_") + ".json"
        filepath = os.path.join(CONFIG_DIR, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            self.project_data = json.load(f)
        self.current_project_file = filepath
        
        # --- AUTO SYNC START ---
        self.sync_project_with_disk()
        # --- AUTO SYNC END ---
        
        return self.project_data

    def scan_for_projects(self):
        """
        Scans TEMPLATE_DIR for subdirectories. 
        1. If a directory exists but no JSON config, create one.
        2. If a JSON config exists but directory is gone, DELETE the config.
        """
        if not os.path.exists(TEMPLATE_DIR):
            return

        # A. DISCOVERY: Find new folders
        for entry in os.listdir(TEMPLATE_DIR):
            full_path = os.path.join(TEMPLATE_DIR, entry)
            if os.path.isdir(full_path):
                safe_name = entry.lower()
                json_filename = safe_name + ".json"
                json_path = os.path.join(CONFIG_DIR, json_filename)
                
                if not os.path.exists(json_path):
                    # Found a folder without a config -> Create it!
                    print(f"Discovered new project folder: {entry}")
                    
                    display_name = entry.replace("_", " ")
                    
                    data = {
                        "project_name": display_name,
                        "project_id": entry, # Use exact folder name as ID
                        "templates": [],
                        "fields": []
                    }
                    try:
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=4, ensure_ascii=False)
                    except Exception as e:
                        print(f"Failed to auto-create config for {entry}: {e}")

        # B. PRUNING: Remove invalid configs
        if os.path.exists(CONFIG_DIR):
            for f_name in os.listdir(CONFIG_DIR):
                if f_name.endswith('.json') and f_name != 'projects_order.json':
                    cfg_path = os.path.join(CONFIG_DIR, f_name)
                    try:
                        # We need to know the project_id to check folder existence
                        # Filename might mismatch project_id if renamed, so rely on content?
                        # Or, rely on our convention that filename matches safe project_id?
                        # Safer to read content.
                        with open(cfg_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        pid = data.get('project_id')
                        if pid:
                            t_dir = os.path.join(TEMPLATE_DIR, pid)
                            if not os.path.exists(t_dir):
                                print(f"Pruning invalid project config: {f_name} (Folder {pid} missing)")
                                f.close() # Close before deleting
                                os.remove(cfg_path)
                                # Also remove from order?
                                self._remove_from_order(data.get('project_name', ''))
                    except Exception as e:
                        print(f"Error pruning config {f_name}: {e}")


    def sync_project_with_disk(self):
        """
        Syncs the current loaded project data with the actual files on disk.
        1. Updates 'templates' list.
        2. Scans for new {{fields}}.
        """
        if not self.project_data:
            return

        pid = self.project_data.get('project_id')
        t_dir = os.path.join(TEMPLATE_DIR, pid)
        
        if not os.path.exists(t_dir):
            # FIX: If directory is gone, the templates are gone.
            # We must update the config to reflect this, otherwise it shows stale entries.
            self.project_data['templates'] = []
            self.project_data['fields'] = [] # Prune fields too
            self.save_current_project()
            return

        # 1. Sync Templates List
        disk_files = [f for f in os.listdir(t_dir) if f.endswith('.docx') and not f.startswith('~$')]
        current_list = self.project_data.get('templates', [])
        
        # Add new
        for f in disk_files:
            if f not in current_list:
                current_list.append(f)
        
        # Remove deleted
        current_list = [f for f in current_list if f in disk_files]
        
        self.project_data['templates'] = current_list
        
        # 2. Sync Fields (Strict Mode: File System is Truth)
        # Scan ALL current templates to get the definitive set of required fields.
        required_fields = set()
        
        for t_name in current_list: # Use the synced list
            t_path = os.path.join(t_dir, t_name)
            fields = extract_fields_from_docx(t_path)
            required_fields.update(fields)
            
        # Update self.project_data['fields']
        # a) Remove fields that are no longer required
        current_fields_list = self.project_data.get('fields', [])
        # Filter to keep only those present in required_fields
        # (We basically rebuild the list, preserving info of existing valid ones)
        
        new_fields_list = []
        valid_ids_processed = set()
        
        for f in current_fields_list:
            fid = f['id']
            if fid in required_fields:
                new_fields_list.append(f)
                valid_ids_processed.add(fid)
        
        # b) Add new fields that were not in existing list
        for fid in required_fields:
            if fid not in valid_ids_processed:
                new_fields_list.append({'id': fid, 'label': fid})
        
        self.project_data['fields'] = new_fields_list
                
        # Save if changed
        # We should save if we modified templates OR fields
        # Ideally check for dirty state, but saving is cheap enough here.
        self.save_current_project()


    def save_current_project(self):
        if self.current_project_file:
            with open(self.current_project_file, 'w', encoding='utf-8') as f:
                json.dump(self.project_data, f, indent=4, ensure_ascii=False)

    def rename_project(self, old_display_name, new_display_name):
        old_safe = old_display_name.lower().replace(" ", "_").replace("/", "").replace("\\", "")
        old_filename = old_safe + ".json"
        old_filepath = os.path.join(CONFIG_DIR, old_filename)
        
        new_safe = new_display_name.lower().replace(" ", "_").replace("/", "").replace("\\", "")
        new_filename = new_safe + ".json"
        new_filepath = os.path.join(CONFIG_DIR, new_filename)
        
        if os.path.exists(new_filepath):
            raise FileExistsError("Target project name already exists.")
            
        # Load logic to find folder
        with open(old_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        old_pid = data.get('project_id', old_safe)
        old_folder = os.path.join(TEMPLATE_DIR, old_pid)
        new_folder = os.path.join(TEMPLATE_DIR, new_safe)
        
        # 1. Rename JSON
        os.rename(old_filepath, new_filepath)
        
        # 2. Rename Folder
        if os.path.exists(old_folder) and not os.path.exists(new_folder):
            os.rename(old_folder, new_folder)
        elif not os.path.exists(new_folder):
            os.makedirs(new_folder, exist_ok=True)
            
        # 3. Update Content
        data['project_name'] = new_display_name
        data['project_id'] = new_safe
        with open(new_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        # 4. Update Order
        self._update_order_entry(old_display_name, new_display_name)
        
        if self.current_project_file == old_filepath:
            self.current_project_file = new_filepath
            self.project_data = data

    def delete_project(self, display_name):
        safe_name = display_name.lower().replace(" ", "_")
        filename = safe_name + ".json"
        filepath = os.path.join(CONFIG_DIR, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            pid = data.get('project_id', safe_name)
            folder = os.path.join(TEMPLATE_DIR, pid)
            if os.path.exists(folder):
                try:
                    shutil.rmtree(folder)
                except OSError as e:
                    import errno
                    if e.errno == errno.EACCES or e.winerror == 32:
                        raise OSError(f"无法删除项目文件夹，因为文件正在被占用。\n请检查是否已打开该项目下的Word文档，关闭后重试。\n({e})")
                    raise e
            try:
                os.remove(filepath)
            except OSError as e:
                # If we couldn't delete the config but deleted the folder? 
                # Or if config is locked?
                raise OSError(f"无法删除项目配置文件。\n({e})")
            
        # Remove from order
        self._remove_from_order(display_name)
        
        if self.current_project_file == filepath:
            self.current_project_file = None
            self.project_data = {}

    def _update_order_entry(self, old_name, new_name):
        order_file = os.path.join(CONFIG_DIR, 'projects_order.json')
        if os.path.exists(order_file):
             with open(order_file, 'r', encoding='utf-8') as Of:
                 current_order = json.load(Of)
             if old_name in current_order:
                 idx = current_order.index(old_name)
                 current_order[idx] = new_name
                 with open(order_file, 'w', encoding='utf-8') as Of:
                      json.dump(current_order, Of, ensure_ascii=False)

    def _remove_from_order(self, name):
        order_file = os.path.join(CONFIG_DIR, 'projects_order.json')
        if os.path.exists(order_file):
             with open(order_file, 'r', encoding='utf-8') as Of:
                 current_order = json.load(Of)
             if name in current_order:
                 current_order.remove(name)
                 with open(order_file, 'w', encoding='utf-8') as Of:
                      json.dump(current_order, Of, ensure_ascii=False)

    def get_template_dir(self):
        if not self.project_data:
            return None
        pid = self.project_data.get('project_id')
        if not pid:
            # Fallback
            safe = self.project_data.get('project_name', 'default').lower().replace(" ", "_")
            pid = safe
        
        path = os.path.join(TEMPLATE_DIR, pid)
        os.makedirs(path, exist_ok=True)
        return path
