"""
Extract actual file contents from webMethods packages
"""

import zipfile
from typing import Dict, Optional

class FileExtractor:
    """Extract raw file contents"""
    
    @staticmethod
    def get_service_files(package_path: str, service_path: str) -> Dict[str, str]:
        """Get all files for a service"""
        
        files = {}
        
        try:
            with zipfile.ZipFile(package_path, 'r') as zf:
                file_list = zf.namelist()
                
                # Get node.ndf
                node_ndf_path = f"{service_path}/node.ndf"
                if node_ndf_path in file_list:
                    content = zf.read(node_ndf_path)
                    try:
                        files['node.ndf'] = content.decode('utf-8', errors='ignore')
                    except:
                        files['node.ndf'] = content.decode('latin-1', errors='ignore')
                
                # Get flow.xml
                flow_xml_path = f"{service_path}/flow.xml"
                if flow_xml_path in file_list:
                    content = zf.read(flow_xml_path)
                    files['flow.xml'] = content.decode('utf-8', errors='ignore')
                
                # Get schema.ndf
                schema_ndf_path = f"{service_path}/schema.ndf"
                if schema_ndf_path in file_list:
                    content = zf.read(schema_ndf_path)
                    try:
                        files['schema.ndf'] = content.decode('utf-8', errors='ignore')
                    except:
                        files['schema.ndf'] = content.decode('latin-1', errors='ignore')
                
                # Get java.frag
                java_frag_path = f"{service_path}/java.frag"
                if java_frag_path in file_list:
                    content = zf.read(java_frag_path)
                    files['java.frag'] = content.decode('utf-8', errors='ignore')
        
        except Exception as e:
            print(f"Error extracting files: {e}")
        
        return files


def get_service_source_files(package_path: str, service_path: str) -> Dict[str, str]:
    """Main function to get service files"""
    extractor = FileExtractor()
    return extractor.get_service_files(package_path, service_path)
