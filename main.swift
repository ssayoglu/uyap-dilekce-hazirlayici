import Cocoa
import WebKit

class AppDelegate: NSObject, NSApplicationDelegate, NSWindowDelegate, WKNavigationDelegate, WKUIDelegate {
    var window: NSWindow!
    var webView: WKWebView!
    var pythonProcess: Process?
    var statusItem: NSStatusItem?

    func applicationDidFinishLaunching(_ notification: Notification) {
        // macOS Standart Kısayolları ve Menü Çubuğu (⌘C, ⌘V, ⌘X, ⌘A, ⌘Z, ⌘Q, ⌘W vb.)
        setupMainMenu()

        let fileManager = FileManager.default
        let homeDir = NSHomeDirectory()
        let targetDir = "\(homeDir)/.dilekce-hazirlayici"

        // 1. Arka Planda Otomatik GitHub Güncellemesi (Her açılışta sessizce son sürümü çeker)
        checkForUpdatesInBackground(targetDir: targetDir)

        let pythonPaths = [
            "/opt/homebrew/bin/python3",
            "/usr/local/bin/python3",
            "/usr/bin/python3"
        ]
        let pythonBinary = pythonPaths.first(where: { fileManager.fileExists(atPath: $0) }) ?? "/usr/bin/python3"

        let possibleServerPaths = [
            "\(targetDir)/server.py",
            Bundle.main.path(forResource: "server", ofType: "py"),
            "\(Bundle.main.bundlePath)/Contents/Resources/server.py",
            "\(Bundle.main.bundlePath)/../server.py",
            "\(FileManager.default.currentDirectoryPath)/server.py",
            "/Users/serkan/Documents/DilekceOlusturucu/server.py"
        ].compactMap { $0 }

        let serverScript = possibleServerPaths.first(where: { fileManager.fileExists(atPath: $0) }) ?? "\(targetDir)/server.py"

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

        // 2. Status bar (Menü çubuğu simgesi)
        setupStatusItem()

        // 3. Window
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
            self.loadWebPage()
        }

        showAppWindow()
    }

    func loadWebPage() {
        if let url = URL(string: "http://127.0.0.1:5678/?t=\(Date().timeIntervalSince1970)") {
            var req = URLRequest(url: url)
            req.cachePolicy = .reloadIgnoringLocalAndRemoteCacheData
            self.webView.load(req)
        }
    }

    // GitHub Otomatik Güncelleme Motoru (Arka planda sessizce çeker)
    func checkForUpdatesInBackground(targetDir: String) {
        DispatchQueue.global(qos: .background).async {
            let fm = FileManager.default
            if fm.fileExists(atPath: "\(targetDir)/.git") {
                let gitTask = Process()
                gitTask.launchPath = "/usr/bin/git"
                gitTask.currentDirectoryPath = targetDir
                gitTask.arguments = ["pull", "--quiet"]
                try? gitTask.run()
                gitTask.waitUntilExit()

                if gitTask.terminationStatus == 0 {
                    // Güncelleme çekildiyse Resources/server.py'yi de senkronize et
                    let appResourcesServer = "\(Bundle.main.bundlePath)/Contents/Resources/server.py"
                    if fm.fileExists(atPath: appResourcesServer) && fm.fileExists(atPath: "\(targetDir)/server.py") {
                        try? fm.removeItem(atPath: appResourcesServer)
                        try? fm.copyItem(atPath: "\(targetDir)/server.py", toPath: appResourcesServer)
                    }
                }
            }
        }
    }

    func setupMainMenu() {
        let mainMenu = NSMenu()

        // 1. Uygulama Menüsü (App Menu)
        let appMenuItem = NSMenuItem()
        mainMenu.addItem(appMenuItem)
        let appMenu = NSMenu()
        appMenuItem.submenu = appMenu
        appMenu.addItem(withTitle: "Hakkında", action: #selector(NSApplication.orderFrontStandardAboutPanel(_:)), keyEquivalent: "")
        appMenu.addItem(withTitle: "Güncellemeleri Denetle", action: #selector(manualUpdateCheck), keyEquivalent: "u")
        appMenu.addItem(NSMenuItem.separator())
        appMenu.addItem(withTitle: "Gizle", action: #selector(NSApplication.hide(_:)), keyEquivalent: "h")
        let hideOthersItem = NSMenuItem(title: "Diğerlerini Gizle", action: #selector(NSApplication.hideOtherApplications(_:)), keyEquivalent: "h")
        hideOthersItem.keyEquivalentModifierMask = [.command, .option]
        appMenu.addItem(hideOthersItem)
        appMenu.addItem(withTitle: "Tümünü Göster", action: #selector(NSApplication.unhideAllApplications(_:)), keyEquivalent: "")
        appMenu.addItem(NSMenuItem.separator())
        appMenu.addItem(withTitle: "Çıkış", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")

        // 2. Düzenle Menüsü (Edit Menu - ⌘C, ⌘V, ⌘X, ⌘A, ⌘Z için zorunludur)
        let editMenuItem = NSMenuItem()
        mainMenu.addItem(editMenuItem)
        let editMenu = NSMenu(title: "Düzenle")
        editMenuItem.submenu = editMenu
        editMenu.addItem(withTitle: "Geri Al", action: Selector(("undo:")), keyEquivalent: "z")
        let redoItem = NSMenuItem(title: "Yinele", action: Selector(("redo:")), keyEquivalent: "Z")
        redoItem.keyEquivalentModifierMask = [.command, .shift]
        editMenu.addItem(redoItem)
        editMenu.addItem(NSMenuItem.separator())
        editMenu.addItem(withTitle: "Kes", action: #selector(NSText.cut(_:)), keyEquivalent: "x")
        editMenu.addItem(withTitle: "Kopyala", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        editMenu.addItem(withTitle: "Yapıştır", action: #selector(NSText.paste(_:)), keyEquivalent: "v")
        editMenu.addItem(withTitle: "Tümünü Seç", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")

        // 3. Pencere Menüsü (Window Menu - ⌘W, ⌘M, ⌘R)
        let windowMenuItem = NSMenuItem()
        mainMenu.addItem(windowMenuItem)
        let windowMenu = NSMenu(title: "Pencere")
        windowMenuItem.submenu = windowMenu
        windowMenu.addItem(withTitle: "Yenile", action: #selector(reloadPage), keyEquivalent: "r")
        windowMenu.addItem(withTitle: "Pencereyi Kapat", action: #selector(NSWindow.performClose(_:)), keyEquivalent: "w")
        windowMenu.addItem(withTitle: "Simge Durumuna Küçült", action: #selector(NSWindow.performMiniaturize(_:)), keyEquivalent: "m")
        windowMenu.addItem(withTitle: "Yakınlaştır", action: #selector(NSWindow.performZoom(_:)), keyEquivalent: "")

        NSApplication.shared.mainMenu = mainMenu
    }

    @objc func reloadPage() {
        loadWebPage()
    }

    @objc func manualUpdateCheck() {
        let homeDir = NSHomeDirectory()
        let targetDir = "\(homeDir)/.dilekce-hazirlayici"
        
        let gitTask = Process()
        gitTask.launchPath = "/usr/bin/git"
        gitTask.currentDirectoryPath = targetDir
        gitTask.arguments = ["pull"]
        try? gitTask.run()
        gitTask.waitUntilExit()

        reloadPage()
        
        let alert = NSAlert()
        alert.messageText = "Güncelleme Kontrolü"
        alert.informativeText = "Uygulama GitHub üzerinden en son sürüme güncellendi ve yenilendi."
        alert.alertStyle = .informational
        alert.runModal()
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
