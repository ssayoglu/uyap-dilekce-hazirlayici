import Cocoa
import WebKit

class AppDelegate: NSObject, NSApplicationDelegate, NSWindowDelegate, WKNavigationDelegate, WKUIDelegate {
    var window: NSWindow!
    var webView: WKWebView!
    var pythonProcess: Process?
    var statusItem: NSStatusItem?

    func applicationDidFinishLaunching(_ notification: Notification) {
        let fileManager = FileManager.default
        let pythonPaths = [
            "/opt/homebrew/bin/python3",
            "/usr/local/bin/python3",
            "/usr/bin/python3"
        ]
        let pythonBinary = pythonPaths.first(where: { fileManager.fileExists(atPath: $0) }) ?? "/usr/bin/python3"

        let homeDir = NSHomeDirectory()
        let possibleServerPaths = [
            Bundle.main.path(forResource: "server", ofType: "py"),
            "\(homeDir)/.dilekce-hazirlayici/server.py",
            "\(Bundle.main.bundlePath)/Contents/Resources/server.py",
            "\(Bundle.main.bundlePath)/../server.py",
            "\(FileManager.default.currentDirectoryPath)/server.py",
            "/Users/serkan/Documents/DilekceOlusturucu/server.py"
        ].compactMap { $0 }

        let serverScript = possibleServerPaths.first(where: { fileManager.fileExists(atPath: $0) }) ?? "\(homeDir)/.dilekce-hazirlayici/server.py"

        // Kill any previous hanging instance on port 5678
        let killTask = Process()
        killTask.launchPath = "/usr/bin/pkill"
        killTask.arguments = ["-f", "server.py"]
        try? killTask.run()
        killTask.waitUntilExit()

        // Start python backend
        let task = Process()
        task.launchPath = pythonBinary
        task.arguments = [serverScript, "--no-browser"]
        try? task.run()
        self.pythonProcess = task

        // 1. Status bar (Menü çubuğu simgesi ve menüsü)
        setupStatusItem()

        // 2. Window (Kapatılınca deallocate olmaması için isReleasedWhenClosed = false)
        let rect = NSRect(x: 0, y: 0, width: 960, height: 880)
        window = NSWindow(
            contentRect: rect,
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )
        window.isReleasedWhenClosed = false
        window.center()
        window.title = "⚖️ UYAP Dilekçe & Şablon Yöneticisi"
        window.delegate = self
        window.minSize = NSSize(width: 800, height: 700)

        // Webview
        let config = WKWebViewConfiguration()
        config.preferences.setValue(true, forKey: "developerExtrasEnabled")
        
        webView = WKWebView(frame: rect, configuration: config)
        webView.navigationDelegate = self
        webView.uiDelegate = self
        webView.autoresizingMask = [.width, .height]
        window.contentView = webView

        // Load URL
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) {
            if let url = URL(string: "http://127.0.0.1:5678/?t=\(Date().timeIntervalSince1970)") {
                var req = URLRequest(url: url)
                req.cachePolicy = .reloadIgnoringLocalAndRemoteCacheData
                self.webView.load(req)
            }
        }

        showAppWindow()
    }

    func setupStatusItem() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        if let button = statusItem?.button {
            button.title = "⚖️"
            button.target = self
            button.action = #selector(statusItemClicked)
        }
    }

    @objc func statusItemClicked() {
        showAppWindow()
    }

    func showAppWindow() {
        if window != nil {
            window.setIsVisible(true)
            window.makeKeyAndOrderFront(nil)
            NSApp.activate(ignoringOtherApps: true)
        }
    }

    // "X" butonuna basıldığında pencereyi yok etmek yerine gizle (hide)
    func windowShouldClose(_ sender: NSWindow) -> Bool {
        sender.orderOut(nil)
        return false
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        webView.evaluateJavaScript("""
            if (typeof initApp === 'function') {
                initApp();
            } else if (typeof renderTemplates === 'function') {
                updateLawyerDisplay();
                renderFavorites();
                renderTemplates();
            }
        """, completionHandler: nil)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return false
    }

    func applicationWillTerminate(_ notification: Notification) {
        pythonProcess?.terminate()
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.run()
