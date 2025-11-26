import zipfile
from pathlib import Path

# Find the uploaded ZIP
upload_dir = Path("uploads")
zip_files = list(upload_dir.glob("*.zip"))

if not zip_files:
    print("No ZIP files found in uploads/")
else:
    for zip_path in zip_files:
        print(f"\n=== {zip_path.name} ===\n")
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            files = zf.namelist()
            print(f"Total files: {len(files)}\n")
            
            # Show first 50 files
            print("First 50 files:")
            for f in files[:50]:
                print(f"  {f}")
            
            print("\n--- Looking for key files ---")
            
            # Count key file types
            flow_xml = [f for f in files if f.endswith('flow.xml')]
            node_ndf = [f for f in files if f.endswith('node.ndf')]
            java_frag = [f for f in files if f.endswith('java.frag')]
            manifest = [f for f in files if 'manifest' in f.lower()]
            
            print(f"\nflow.xml files: {len(flow_xml)}")
            for f in flow_xml[:10]:
                print(f"  {f}")
            
            print(f"\nnode.ndf files: {len(node_ndf)}")
            for f in node_ndf[:10]:
                print(f"  {f}")
            
            print(f"\njava.frag files: {len(java_frag)}")
            for f in java_frag[:5]:
                print(f"  {f}")
            
            print(f"\nmanifest files: {len(manifest)}")
            for f in manifest:
                print(f"  {f}")
            
            # Show sample flow.xml content
            if flow_xml:
                print(f"\n--- Sample flow.xml content ---")
                try:
                    content = zf.read(flow_xml[0]).decode('utf-8', errors='ignore')[:1000]
                    print(content)
                except Exception as e:
                    print(f"Error reading: {e}")
