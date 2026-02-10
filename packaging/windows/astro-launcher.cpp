// ASTRO Windows Launcher
// A native Windows application that launches ASTRO in various modes

#include <windows.h>
#include <string>
#include <vector>
#include <filesystem>
#include <fstream>
#include <shlobj.h>
#include <shlwapi.h>

#pragma comment(lib, "shell32.lib")
#pragma comment(lib, "shlwapi.lib")

namespace fs = std::filesystem;

std::wstring GetExecutablePath() {
    wchar_t buffer[MAX_PATH];
    GetModuleFileNameW(NULL, buffer, MAX_PATH);
    return std::wstring(buffer);
}

std::wstring GetExecutableDirectory() {
    std::wstring path = GetExecutablePath();
    size_t lastSlash = path.find_last_of(L"\\/");
    if (lastSlash != std::wstring::npos) {
        return path.substr(0, lastSlash);
    }
    return path;
}

std::wstring GetUserProfilePath() {
    wchar_t buffer[MAX_PATH];
    if (SUCCEEDED(SHGetFolderPathW(NULL, CSIDL_PROFILE, NULL, 0, buffer))) {
        return std::wstring(buffer);
    }
    return L"";
}

std::wstring GetLocalAppDataPath() {
    wchar_t buffer[MAX_PATH];
    if (SUCCEEDED(SHGetFolderPathW(NULL, CSIDL_LOCAL_APPDATA, NULL, 0, buffer))) {
        return std::wstring(buffer);
    }
    return L"";
}

bool DirectoryExists(const std::wstring& path) {
    DWORD attribs = GetFileAttributesW(path.c_str());
    return (attribs != INVALID_FILE_ATTRIBUTES && (attribs & FILE_ATTRIBUTE_DIRECTORY));
}

bool FileExists(const std::wstring& path) {
    DWORD attribs = GetFileAttributesW(path.c_str());
    return (attribs != INVALID_FILE_ATTRIBUTES && !(attribs & FILE_ATTRIBUTE_DIRECTORY));
}

void CreateDirectoryRecursive(const std::wstring& path) {
    if (path.empty() || DirectoryExists(path)) {
        return;
    }
    
    size_t pos = 0;
    do {
        pos = path.find_first_of(L"\\/", pos + 1);
        std::wstring subdir = (pos == std::wstring::npos) ? path : path.substr(0, pos);
        if (!subdir.empty()) {
            CreateDirectoryW(subdir.c_str(), NULL);
        }
    } while (pos != std::wstring::npos);
}

void LaunchWebMode(const std::wstring& appDir, const std::wstring& configDir) {
    std::wstring nodePath = appDir + L"\\nodejs\\node.exe";
    std::wstring serverScript = appDir + L"\\dist\\index.js";
    std::wstring logsDir = configDir + L"\\logs";
    
    CreateDirectoryRecursive(logsDir);
    
    // Set up environment
    std::wstring env = L"NODE_ENV=production\0";
    env += L"PORT=5000\0";
    env += L"ASTRO_HOME=" + appDir + L"\0";
    env += L"\0";
    
    // Start server process
    STARTUPINFOW si = { sizeof(si) };
    PROCESS_INFORMATION pi = {};
    
    std::wstring cmdLine = L"\"" + nodePath + L"\" \"" + serverScript + L"\"";
    
    BOOL success = CreateProcessW(
        NULL,
        &cmdLine[0],
        NULL,
        NULL,
        FALSE,
        CREATE_NO_WINDOW | CREATE_UNICODE_ENVIRONMENT,
        &env[0],
        appDir.c_str(),
        &si,
        &pi
    );
    
    if (success) {
        // Wait a moment for server to start
        Sleep(3000);
        
        // Open browser
        ShellExecuteW(NULL, L"open", L"http://localhost:5000", NULL, NULL, SW_SHOWNORMAL);
        
        // Show info dialog
        MessageBoxW(NULL, 
            L"ASTRO server is running at http://localhost:5000\n\n"
            L"The browser has been opened automatically.\n"
            L"Close this dialog will NOT stop the server.",
            L"ASTRO AI Assistant",
            MB_OK | MB_ICONINFORMATION);
        
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    } else {
        MessageBoxW(NULL, 
            L"Failed to start ASTRO server. Please check the installation.",
            L"Error",
            MB_OK | MB_ICONERROR);
    }
}

void LaunchTUIMode(const std::wstring& appDir, const std::wstring& configDir) {
    std::wstring pythonPath = appDir + L"\\python\\python.exe";
    std::wstring astroPy = appDir + L"\\astro.py";
    
    if (!FileExists(pythonPath)) {
        MessageBoxW(NULL, 
            L"Python runtime not found. Please reinstall ASTRO.",
            L"Error",
            MB_OK | MB_ICONERROR);
        return;
    }
    
    // Start server in background
    std::wstring nodePath = appDir + L"\\nodejs\\node.exe";
    std::wstring serverScript = appDir + L"\\dist\\index.js";
    
    STARTUPINFOW siServer = { sizeof(siServer) };
    PROCESS_INFORMATION piServer = {};
    
    std::wstring serverCmd = L"\"" + nodePath + L"\" \"" + serverScript + L"\"";
    
    BOOL serverStarted = CreateProcessW(
        NULL,
        &serverCmd[0],
        NULL,
        NULL,
        FALSE,
        CREATE_NO_WINDOW,
        NULL,
        appDir.c_str(),
        &siServer,
        &piServer
    );
    
    if (serverStarted) {
        Sleep(2000);
    }
    
    // Launch TUI
    ShellExecuteW(NULL, L"open", pythonPath.c_str(), astroPy.c_str(), appDir.c_str(), SW_SHOWNORMAL);
    
    if (serverStarted) {
        CloseHandle(piServer.hProcess);
        CloseHandle(piServer.hThread);
    }
}

void LaunchCLIMode(const std::wstring& appDir, const std::wstring& configDir) {
    std::wstring pythonPath = appDir + L"\\python\\python.exe";
    std::wstring astroPy = appDir + L"\\astro.py";
    
    if (!FileExists(pythonPath)) {
        MessageBoxW(NULL, 
            L"Python runtime not found. Please reinstall ASTRO.",
            L"Error",
            MB_OK | MB_ICONERROR);
        return;
    }
    
    // Start server in background
    std::wstring nodePath = appDir + L"\\nodejs\\node.exe";
    std::wstring serverScript = appDir + L"\\dist\\index.js";
    
    STARTUPINFOW siServer = { sizeof(siServer) };
    PROCESS_INFORMATION piServer = {};
    
    std::wstring serverCmd = L"\"" + nodePath + L"\" \"" + serverScript + L"\"";
    
    BOOL serverStarted = CreateProcessW(
        NULL,
        &serverCmd[0],
        NULL,
        NULL,
        FALSE,
        CREATE_NO_WINDOW,
        NULL,
        appDir.c_str(),
        &siServer,
        &piServer
    );
    
    if (serverStarted) {
        Sleep(2000);
    }
    
    // Launch CLI with --cli flag
    std::wstring params = L"astro.py --cli";
    
    AllocConsole();
    ShellExecuteW(NULL, L"open", pythonPath.c_str(), params.c_str(), appDir.c_str(), SW_SHOWNORMAL);
    
    if (serverStarted) {
        CloseHandle(piServer.hProcess);
        CloseHandle(piServer.hThread);
    }
}

int WINAPI wWinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPWSTR lpCmdLine, int nCmdShow) {
    std::wstring appDir = GetExecutableDirectory();
    std::wstring configDir = GetLocalAppDataPath() + L"\\ASTRO";
    
    CreateDirectoryRecursive(configDir);
    
    // Parse command line
    std::wstring cmdLine = lpCmdLine;
    
    // Check for mode selection
    if (cmdLine.find(L"--mode=web") != std::wstring::npos) {
        LaunchWebMode(appDir, configDir);
    } else if (cmdLine.find(L"--mode=tui") != std::wstring::npos) {
        LaunchTUIMode(appDir, configDir);
    } else if (cmdLine.find(L"--mode=cli") != std::wstring::npos) {
        LaunchCLIMode(appDir, configDir);
    } else {
        // Show mode selection dialog
        int result = MessageBoxW(NULL,
            L"Welcome to ASTRO AI Assistant!\n\n"
            L"Select launch mode:\n\n"
            L"Yes = Web Mode (opens browser)\n"
            L"No = Terminal UI Mode\n"
            L"Cancel = CLI Mode",
            L"ASTRO AI Assistant",
            MB_YESNOCANCEL | MB_ICONQUESTION);
        
        switch (result) {
            case IDYES:
                LaunchWebMode(appDir, configDir);
                break;
            case IDNO:
                LaunchTUIMode(appDir, configDir);
                break;
            case IDCANCEL:
                LaunchCLIMode(appDir, configDir);
                break;
        }
    }
    
    return 0;
}
