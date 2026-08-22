import Cocoa
import WebKit

class AppDelegate: NSObject, NSApplicationDelegate, NSWindowDelegate {
    var window: NSWindow!
    var webView: WKWebView!
    var pythonProcess: Process?

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Locate python3
        let fileManager = FileManager.default
        let pythonPaths = [
            "/opt/homebrew/bin/python3",
            "/usr/local/bin/python3",
            "/usr/bin/python3"
        ]
        let pythonBinary = pythonPaths.first(where: { fileManager.fileExists(atPath: $0) }) ?? "/usr/bin/python3"

        // Locate server.py
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

        // Start python backend
        let task = Process()
        task.launchPath = pythonBinary
        task.arguments = [serverScript, "--no-browser"]
        try? task.run()
        self.pythonProcess = task

        // Create native macOS window
        let rect = NSRect(x: 0, y: 0, width: 920, height: 860)
        window = NSWindow(
            contentRect: rect,
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )
        window.center()
        window.title = "⚖️ UYAP Dilekçe & Şablon Yöneticisi"
        window.delegate = self
        window.minSize = NSSize(width: 800, height: 700)

        let config = WKWebViewConfiguration()
        webView = WKWebView(frame: rect, configuration: config)
        webView.autoresizingMask = [.width, .height]
        window.contentView = webView

        // Load UI
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.35) {
            if let url = URL(string: "http://127.0.0.1:5678") {
                self.webView.load(URLRequest(url: url))
            }
        }

        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return true
    }

    func applicationWillTerminate(_ notification: Notification) {
        pythonProcess?.terminate()
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.run()
