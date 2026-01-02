#!/bin/bash

# transh Installation Script - Refactored Version
# Fixes PyInstaller PKG archive loading errors

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEFAULT_DOWNLOAD_URL="https://nas.dyyapp.space/d/nas/guest/app/transh?sign=aRliC0UYDfAD3_-40dck43tPBhA9ZD77r77w2_oIeko=:0"
DOWNLOAD_URL="${TRANSH_DOWNLOAD_URL:-${DEFAULT_DOWNLOAD_URL}}"
INSTALL_DIR="/usr/local/bin"
BINARY_NAME="transh"
INSTALL_PATH="${INSTALL_DIR}/${BINARY_NAME}"
MIN_BINARY_SIZE=$((5 * 1024 * 1024)) # 5MB minimum size

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script requires root privileges."
        echo "Please run with sudo: sudo bash $0"
        exit 1
    fi
}

# Function to check dependencies
check_dependencies() {
    local missing_deps=""
    
    # Check for curl or wget
    if ! command -v curl > /dev/null 2>&1 && ! command -v wget > /dev/null 2>&1; then
        missing_deps="curl or wget"
    fi
    
    # Check for other essential tools
    for tool in file chmod cp rm; do
        if ! command -v $tool > /dev/null 2>&1; then
            missing_deps="${missing_deps} $tool"
        fi
    done
    
    if [ -n "${missing_deps}" ]; then
        print_error "Missing dependencies: ${missing_deps}"
        echo ""
        echo "Please install them first:"
        echo "  Ubuntu/Debian: sudo apt update && sudo apt install curl file"
        echo "  CentOS/RHEL:   sudo yum install curl file"
        echo "  macOS:         brew install curl"
        exit 1
    fi
}

# Function to validate binary file
validate_binary() {
    local file_path="$1"
    
    # Check if file exists and has content
    if [ ! -f "${file_path}" ]; then
        print_error "File does not exist: ${file_path}"
        return 1
    fi
    
    if [ ! -s "${file_path}" ]; then
        print_error "File is empty: ${file_path}"
        return 1
    fi
    
    # Check minimum size
    local file_size=$(stat -c%s "${file_path}" 2>/dev/null || stat -f%z "${file_path}" 2>/dev/null || echo "0")
    if [ "${file_size}" -lt "${MIN_BINARY_SIZE}" ]; then
        print_error "File is too small (${file_size} bytes), expected at least ${MIN_BINARY_SIZE} bytes"
        return 1
    fi
    
    # Check if it's a valid ELF executable
    local file_type=$(file -b "${file_path}" 2>/dev/null || echo "unknown")
    if echo "${file_type}" | grep -qi "ELF.*executable"; then
        print_success "Valid ELF executable detected (${file_size} bytes)"
        return 0
    elif echo "${file_type}" | grep -qi "text\|json\|html"; then
        print_error "File appears to be text/HTML/JSON, not a binary executable"
        echo "File type: ${file_type}"
        # Show first few lines for debugging
        echo "First 3 lines:"
        head -n 3 "${file_path}"
        return 1
    else
        print_warning "File type: ${file_type}"
        print_warning "File may not be a standard ELF executable, but continuing..."
        return 0
    fi
}

# Function to test binary execution
test_binary() {
    local binary_path="$1"
    
    print_info "Testing binary execution..."
    
    # Test with --help flag
    if "${binary_path}" --help >/dev/null 2>&1; then
        print_success "Binary test passed (--help works)"
        return 0
    else
        # Try to capture error
        local error_output
        error_output=$("${binary_path}" --help 2>&1 || true)
        
        if echo "${error_output}" | grep -qi "PYI-.*ERROR.*Could not load PyInstaller"; then
            print_error "PyInstaller PKG archive loading error detected:"
            echo "${error_output}" | grep -i "PYI-"
            return 1
        else
            print_warning "Binary test failed, but may still work"
            echo "Error output: ${error_output:0:200}"
            return 0
        fi
    fi
}

# Function to download with robust error handling
download_file() {
    local url="$1"
    local output_path="$2"
    local max_retries=3
    local retry_count=0
    local download_success=false
    
    while [ ${retry_count} -lt ${max_retries} ]; do
        retry_count=$((retry_count + 1))
        
        if [ ${retry_count} -gt 1 ]; then
            print_info "Retry ${retry_count}/${max_retries}..."
            sleep 2
        fi
        
        # Clean up any existing file
        rm -f "${output_path}"
        
        # Try curl first, then wget
        if command -v curl > /dev/null 2>&1; then
            print_info "Downloading with curl (attempt ${retry_count})..."
            if curl -L "${url}" -o "${output_path}" --progress-bar --fail --retry 2 --retry-delay 1; then
                download_success=true
            else
                print_error "curl download failed"
                continue
            fi
        elif command -v wget > /dev/null 2>&1; then
            print_info "Downloading with wget (attempt ${retry_count})..."
            if wget "${url}" -O "${output_path}" -q --tries=2; then
                download_success=true
            else
                print_error "wget download failed"
                continue
            fi
        fi
        
        # Validate the downloaded file
        if [ "${download_success}" = true ] && validate_binary "${output_path}"; then
            print_success "Download completed successfully"
            return 0
        else
            download_success=false
            rm -f "${output_path}"
        fi
    done
    
    print_error "Download failed after ${max_retries} attempts"
    return 1
}

# Function to install binary with validation
install_binary() {
    local source_path="$1"
    local dest_path="$2"
    
    print_info "Installing binary to ${dest_path}..."
    
    # Backup existing file if it exists
    if [ -f "${dest_path}" ]; then
        local backup_path="${dest_path}.backup.$(date +%s)"
        cp -f "${dest_path}" "${backup_path}"
        print_info "Backed up existing binary to ${backup_path}"
    fi
    
    # Copy with preserve mode
    cp -f "${source_path}" "${dest_path}"
    
    # Set executable permissions
    chmod 755 "${dest_path}"
    
    # Verify the installed file
    if validate_binary "${dest_path}"; then
        print_success "Binary installed successfully"
        
        # Test the installed binary
        if test_binary "${dest_path}"; then
            print_success "Installation verification passed"
            return 0
        else
            print_error "Installation verification failed"
            # Restore backup if available
            if [ -f "${backup_path}" ]; then
                print_info "Restoring from backup..."
                cp -f "${backup_path}" "${dest_path}"
                chmod 755 "${dest_path}"
            fi
            return 1
        fi
    else
        print_error "Installation failed: binary validation error"
        # Restore backup if available
        if [ -f "${backup_path}" ]; then
            print_info "Restoring from backup..."
            cp -f "${backup_path}" "${dest_path}"
            chmod 755 "${dest_path}"
        fi
        return 1
    fi
}

# Main installation function
install_transh() {
    echo ""
    echo "========================================="
    echo "  transh Installation (Refactored)"
    echo "========================================="
    echo ""
    
    check_root
    check_dependencies
    
    # Check if already installed
    if [ -f "${INSTALL_PATH}" ]; then
        print_warning "transh is already installed at ${INSTALL_PATH}"
        read -p "Do you want to reinstall? (y/N): " -r
        echo
        if [ "${REPLY}" != "y" ] && [ "${REPLY}" != "Y" ]; then
            print_info "Installation cancelled"
            exit 0
        fi
    fi
    
    # Create temp directory for download
    local temp_dir=$(mktemp -d)
    local temp_file="${temp_dir}/transh_download"
    
    # Clean up temp directory on exit
    trap "rm -rf '${temp_dir}'" EXIT
    
    # Download transh
    print_info "Downloading transh..."
    if ! download_file "${DOWNLOAD_URL}" "${temp_file}"; then
        print_error "Download failed"
        echo ""
        print_warning "Alternative installation options:"
        echo "  1. Use local file: sudo $0 install-local /path/to/transh"
        echo "  2. Build from source: python -m PyInstaller transh.spec"
        exit 1
    fi
    
    # Install the binary
    if install_binary "${temp_file}" "${INSTALL_PATH}"; then
        print_success "transh installed successfully!"
        
        # Verify PATH availability
        if command -v transh > /dev/null 2>&1; then
            print_success "transh is now available in your PATH"
            
            # Configuration instructions
            echo ""
            print_info "Configuration required before use:"
            print_info "Run 'transh -c' to configure API settings"
            echo ""
            print_success "Installation completed successfully!"
            echo ""
            echo "Usage examples:"
            echo "  transh \"npm -h\"       # Translate command output"
            echo "  transh -t \"hello\"     # Translate text directly"
            echo "  transh -h              # Show help"
        else
            print_warning "transh installed but may not be in PATH"
            echo "You can run it directly: ${INSTALL_PATH}"
        fi
    else
        print_error "Installation failed"
        exit 1
    fi
}

# Function to install from local file
install_local() {
    local local_file="$1"
    
    echo ""
    echo "========================================="
    echo "  transh Installation (Local File)"
    echo "========================================="
    echo ""
    
    check_root
    
    if [ -z "${local_file}" ]; then
        print_error "No file path provided"
        echo "Usage: $0 install-local /path/to/transh"
        exit 1
    fi
    
    if [ ! -f "${local_file}" ]; then
        print_error "File not found: ${local_file}"
        exit 1
    fi
    
    # Validate the local file
    if ! validate_binary "${local_file}"; then
        print_error "Local file validation failed"
        exit 1
    fi
    
    # Install the binary
    if install_binary "${local_file}" "${INSTALL_PATH}"; then
        print_success "transh installed successfully from local file!"
        
        # Verify PATH availability
        if command -v transh > /dev/null 2>&1; then
            print_success "transh is now available in your PATH"
        fi
    else
        print_error "Installation failed"
        exit 1
    fi
}

# Function to uninstall
uninstall_transh() {
    echo ""
    echo "========================================="
    echo "  transh Uninstallation"
    echo "========================================="
    echo ""
    
    check_root
    
    if [ ! -f "${INSTALL_PATH}" ]; then
        print_warning "transh is not installed"
        exit 0
    fi
    
    read -p "Are you sure you want to uninstall transh? (y/N): " -r
    echo
    if [ "${REPLY}" != "y" ] && [ "${REPLY}" != "Y" ]; then
        print_info "Uninstallation cancelled"
        exit 0
    fi
    
    # Remove binary
    print_info "Removing ${INSTALL_PATH}..."
    rm -f "${INSTALL_PATH}"
    
    # Check if removal was successful
    if [ ! -f "${INSTALL_PATH}" ]; then
        print_success "transh uninstalled successfully"
        
        # Ask about configuration files
        echo ""
        read -p "Remove configuration and cache files? (y/N): " -r
        echo
        if [ "${REPLY}" = "y" ] || [ "${REPLY}" = "Y" ]; then
            local user_home=""
            if [ -n "$SUDO_USER" ]; then
                user_home=$(eval echo ~${SUDO_USER})
            else
                user_home="${HOME}"
            fi
            
            print_info "Removing configuration files..."
            rm -rf "${user_home}/.transh_config.json" \
                   "${user_home}/.transh_cache" \
                   "${user_home}/.transh_lang.json" 2>/dev/null || true
            print_success "Configuration files removed"
        fi
    else
        print_error "Failed to remove ${INSTALL_PATH}"
        exit 1
    fi
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  install              Install transh from default URL"
    echo "  install-local FILE   Install transh from local file"
    echo "  uninstall            Uninstall transh"
    echo "  help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  sudo $0 install"
    echo "  sudo $0 install-local ./dist/transh"
    echo "  sudo $0 uninstall"
}

# Main function
main() {
    case "${1}" in
        install)
            install_transh
            ;;
        install-local)
            install_local "${2}"
            ;;
        uninstall)
            uninstall_transh
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            # Interactive mode
            echo ""
            echo "transh Installer"
            echo "================"
            echo ""
            echo "1) Install transh (download from URL)"
            echo "2) Install transh (from local file)"
            echo "3) Uninstall transh"
            echo "4) Show help"
            echo "5) Exit"
            echo ""
            
            read -p "Select option (1-5): " choice
            case ${choice} in
                1)
                    install_transh
                    ;;
                2)
                    read -p "Enter path to transh binary: " local_file
                    install_local "${local_file}"
                    ;;
                3)
                    uninstall_transh
                    ;;
                4)
                    show_help
                    ;;
                5)
                    exit 0
                    ;;
                *)
                    print_error "Invalid option"
                    exit 1
                    ;;
            esac
            ;;
    esac
}

# Handle interrupts
trap 'echo ""; print_info "Interrupted by user"; exit 130' INT

# Run main
main "$@"
