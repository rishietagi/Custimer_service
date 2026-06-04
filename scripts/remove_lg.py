import os
import re

WORKSPACE_DIR = "."
EXCLUDE_DIRS = [".git", ".gemini", "node_modules", ".system_generated"]

REPLACEMENTS = {
    # Brand and company names
    "SmartCare": "SmartCare",
    "SmartCare": "SmartCare",
    "Signature Red": "Signature Red",
    "Signature": "Signature",
    "Certified Tech": "Certified Tech",
    "Certified": "Certified",
    "Installation Team": "Installation Team",
    "Installation": "Installation",
    "ORD-": "ORD-",
    "ORD": "ORD",
    "support-example.com": "support-example.com",
    "appliances": "appliances",
    "appliance": "appliance",
    "OLED": "OLED",
    "NeoChef": "NeoChef",
    "QuadWash": "QuadWash",
    "Brand Logo": "Brand Logo",
    "support portal": "support portal",
    "SmartCare API": "SmartCare API",
    "SmartCare Assistant": "SmartCare Assistant",
    "Brand": "Brand",
    "SmartCare": "SmartCare", # fallback
}

def remove_brand_references():
    print("Starting brand references cleanup...")
    count_files = 0
    count_replacements = 0
    
    for root, dirs, files in os.walk(WORKSPACE_DIR):
        # Exclude directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext not in [".tsx", ".ts", ".py", ".md", ".html", ".css", ".json"]:
                continue
                
            path = os.path.join(root, file)
            
            # Read file
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try fallback encoding
                try:
                    with open(path, "r", encoding="latin-1") as f:
                        content = f.read()
                except Exception:
                    continue
            
            # Perform specific logo image replacements first
            original_content = content
            
            # 1. Sidebar.tsx logo replace
            if "Sidebar.tsx" in file:
                content = content.replace(
                    '<img \n            src="https://www.smartcare.com/smartcare5-common-gp/images/header/logo.png" \n            alt="Brand Logo" \n            className="w-16 h-auto mb-2 object-contain" \n          />',
                    '<div className="w-12 h-12 bg-brand-red/10 rounded-xl flex items-center justify-center mb-2">\n            <Sparkles className="w-6 h-6 text-brand-red" />\n          </div>'
                )
                content = content.replace(
                    'MessageSquare, Calendar, Package, User, LogOut',
                    'MessageSquare, Calendar, Package, User, LogOut, Sparkles'
                )
            
            # 2. Navbar.tsx logo replace
            if "Navbar.tsx" in file:
                content = content.replace(
                    '<img \n            src="https://www.smartcare.com/smartcare5-common-gp/images/header/logo.png" \n            alt="Brand Logo" \n            className="w-10 h-auto object-contain"\n          />',
                    '<div className="w-8 h-8 bg-brand-red/10 rounded-smartcare flex items-center justify-center">\n            <Sparkles className="w-4 h-4 text-brand-red" />\n          </div>'
                )
                content = content.replace(
                    'Menu, X, LogOut, MessageSquare, Calendar, Package, User',
                    'Menu, X, LogOut, MessageSquare, Calendar, Package, User, Sparkles'
                )
            
            # 3. Login.tsx logo replace
            if "Login.tsx" in file:
                content = content.replace(
                    '<img \n            src="https://www.smartcare.com/smartcare5-common-gp/images/header/logo.png" \n            alt="Brand Logo" \n            className="w-20 h-auto mb-3 invert brightness-0" \n          />',
                    '<div className="w-12 h-12 bg-white/10 rounded-full flex items-center justify-center mb-3">\n            <Sparkles className="w-6 h-6 text-white" />\n          </div>'
                )
                content = content.replace(
                    'Shield, Key, UserPlus, FileText, AlertCircle',
                    'Shield, Key, UserPlus, FileText, AlertCircle, Sparkles'
                )
            
            # 4. ChatAssistant.tsx logo replace
            if "ChatAssistant.tsx" in file:
                content = content.replace(
                    '<img \n                      src="https://www.smartcare.com/smartcare5-common-gp/images/header/logo.png" \n                      alt="Brand Logo" \n                      className="w-5 h-auto object-contain invert brightness-0" \n                    />',
                    '<Sparkles className="w-4 h-4 text-white" />'
                )
                content = content.replace(
                    '<img \n                src="https://www.smartcare.com/smartcare5-common-gp/images/header/logo.png" \n                alt="Brand Logo" \n                className="w-5 h-auto object-contain invert brightness-0" \n              />',
                    '<Sparkles className="w-4 h-4 text-white" />'
                )
            
            # 5. login.py (Streamlit) logo replace
            if "login.py" in file:
                content = content.replace(
                    'st.image("https://www.smartcare.com/smartcare5-common-gp/images/header/logo.png", width=120)',
                    'st.write("🔒")'
                )
                
            # Perform text replacements
            for orig, rep in REPLACEMENTS.items():
                content = re.sub(r'\b' + re.escape(orig) + r'\b', rep, content)
                content = re.sub(re.escape(orig.lower()), rep.lower(), content)
                content = re.sub(re.escape(orig.upper()), rep.upper(), content)
            
            # Write back if changed
            if content != original_content:
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"Cleaned references in: {path}")
                    count_files += 1
                except Exception as e:
                    print(f"Error writing to {path}: {e}")
                    
    print(f"Cleanup finished. Updated {count_files} files.")

if __name__ == "__main__":
    remove_brand_references()
