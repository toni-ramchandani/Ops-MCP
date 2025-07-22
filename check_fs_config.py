#!/usr/bin/env python3
"""
Check current filesystem configuration for the MCP server
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_fs_config():
    """Check and display current filesystem configuration"""
    
    # Get the raw environment variable
    raw_dirs = os.getenv("FS_ALLOWED_DIRS", "").strip()
    print(f"FS_ALLOWED_DIRS environment variable: '{raw_dirs}'")
    
    if not raw_dirs:
        print("\n❌ FS_ALLOWED_DIRS is empty or not set!")
        print("📁 Default allowed directory: Current working directory only")
        print(f"   → {Path.cwd().resolve()}")
    else:
        print(f"\n✅ FS_ALLOWED_DIRS is set")
        dirs = [p.strip() for p in raw_dirs.split(os.pathsep) if p.strip()]
        print(f"📁 Number of allowed directories: {len(dirs)}")
        
        for i, d in enumerate(dirs, 1):
            p = Path(d).expanduser().resolve()
            exists = "✅" if p.exists() else "❌"
            print(f"   {i}. {exists} {p}")
    
    # Check if Downloads directory would be allowed
    downloads_path = Path(r"C:\Users\ramcton\Downloads")
    print(f"\n🔍 Downloads directory check:")
    print(f"   Path: {downloads_path}")
    print(f"   Exists: {'✅' if downloads_path.exists() else '❌'}")
    
    # Test if Downloads would be accessible
    if raw_dirs:
        allowed_dirs = [Path(p.strip()).expanduser().resolve() 
                       for p in raw_dirs.split(os.pathsep) if p.strip()]
        
        would_allow = any(
            downloads_path == allowed_dir or downloads_path.is_relative_to(allowed_dir)
            for allowed_dir in allowed_dirs
        )
        print(f"   Would be accessible: {'✅' if would_allow else '❌'}")
    else:
        print(f"   Would be accessible: ❌ (no FS_ALLOWED_DIRS set)")

if __name__ == "__main__":
    print("🔧 MCP Server Filesystem Configuration Check")
    print("=" * 50)
    check_fs_config()
    
    print(f"\n💡 To fix access to Downloads:")
    print(f"   Add this to your .env file:")
    print(f"   FS_ALLOWED_DIRS=C:\\Users\\ramcton\\Downloads;C:\\Users\\ramcton\\Desktop;C:\\Users\\ramcton\\Documents") 