"""
Dashboard Builder Test Wrapper
- Runs the Dashboard builder in isolated mode (outputting to a temporary directory).
"""
import os
import sys
import shutil
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')

try:
    from Dashboard import builder
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    print(f"🧪 Testing build in temp dir: {temp_dir}")
    
    try:
        # Run build
        builder.build(output_dir=temp_dir)
        
        # Verify output
        index_path = os.path.join(temp_dir, 'index.html')
        if os.path.exists(index_path):
            print("✅ Build successful: index.html found.")
        else:
            print("❌ Build failed: index.html not found.")
            sys.exit(1)
            
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print(f"🧹 Cleaned up temp dir: {temp_dir}")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
