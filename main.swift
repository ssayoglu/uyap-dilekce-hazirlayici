import Cocoa
import WebKit

class AppDelegate: NSObject, NSApplicationDelegate, NSWindowDelegate, WKNavigationDelegate, WKUIDelegate {
    var window: NSWindow!
    var webView: WKWebView!
    var pythonProcess: Process?
    var statusItem: NSStatusItem?
    var popover: NSPopover?
    var popoverWebView: WKWebView?
    var targetDir: String = ""

    func applicationDidFinishLaunching(_ notification: Notification) {
        setupMainMenu()

        let homeDir = NSHomeDirectory()
        self.targetDir = "\(homeDir)/.dilekce-hazirlayici"

        checkForUpdatesInBackground(targetDir: self.targetDir)
        startPythonServer(targetDir: self.targetDir)

        // 2. Status Bar & Popover Setup
        setupStatusItem()

        // 3. Main App Window
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

        let config = WKWebViewConfiguration()
        config.preferences.setValue(true, forKey: "developerExtrasEnabled")
        
        webView = WKWebView(frame: rect, configuration: config)
        webView.navigationDelegate = self
        webView.uiDelegate = self
        webView.autoresizingMask = [.width, .height]
        window.contentView = webView

        DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) {
            self.loadWebPage()
        }

        showAppWindow()
    }

    func startPythonServer(targetDir: String) {
        let fileManager = FileManager.default
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

        let killTask = Process()
        killTask.launchPath = "/usr/bin/pkill"
        killTask.arguments = ["-f", "server.py"]
        try? killTask.run()
        killTask.waitUntilExit()

        Thread.sleep(forTimeInterval: 0.2)

        let task = Process()
        task.launchPath = pythonBinary
        task.arguments = [serverScript, "--no-browser"]
        try? task.run()
        self.pythonProcess = task
    }

    func loadWebPage() {
        if let url = URL(string: "http://127.0.0.1:5678/?t=\(Date().timeIntervalSince1970)") {
            var req = URLRequest(url: url)
            req.cachePolicy = .reloadIgnoringLocalAndRemoteCacheData
            self.webView.load(req)
        }
    }

    func getCurrentVersion(targetDir: String) -> String {
        let possibleVersionPaths = [
            "\(targetDir)/version.json",
            Bundle.main.path(forResource: "version", ofType: "json"),
            "\(Bundle.main.bundlePath)/Contents/Resources/version.json"
        ].compactMap { $0 }
        
        for path in possibleVersionPaths {
            if let data = try? Data(contentsOf: URL(fileURLWithPath: path)),
               let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let ver = json["version"] as? String {
                return ver
            }
        }
        return "1.5.0"
    }

    func isVersion(_ v1: String, greaterThan v2: String) -> Bool {
        let parts1 = v1.split(separator: ".").compactMap { Int($0) }
        let parts2 = v2.split(separator: ".").compactMap { Int($0) }
        for i in 0..<max(parts1.count, parts2.count) {
            let p1 = i < parts1.count ? parts1[i] : 0
            let p2 = i < parts2.count ? parts2[i] : 0
            if p1 > p2 { return true }
            if p1 < p2 { return false }
        }
        return false
    }

    func checkForUpdatesInBackground(targetDir: String) {
        DispatchQueue.global(qos: .background).async {
            guard let url = URL(string: "https://raw.githubusercontent.com/ssayoglu/uyap-dilekce-hazirlayici/main/version.json?t=\(Date().timeIntervalSince1970)") else { return }
            var request = URLRequest(url: url)
            request.cachePolicy = .reloadIgnoringLocalAndRemoteCacheData
            request.timeoutInterval = 4.0

            let task = URLSession.shared.dataTask(with: request) { [weak self] data, _, err in
                guard let self = self, let data = data, err == nil,
                      let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                      let remoteVersion = json["version"] as? String else { return }

                let localVersion = self.getCurrentVersion(targetDir: targetDir)
                if self.isVersion(remoteVersion, greaterThan: localVersion) {
                    if let rawServerUrl = URL(string: "https://raw.githubusercontent.com/ssayoglu/uyap-dilekce-hazirlayici/main/server.py"),
                       let serverData = try? Data(contentsOf: rawServerUrl) {
                        let fm = FileManager.default
                        try? fm.createDirectory(atPath: targetDir, withIntermediateDirectories: true)
                        try? serverData.write(to: URL(fileURLWithPath: "\(targetDir)/server.py"))
                        try? data.write(to: URL(fileURLWithPath: "\(targetDir)/version.json"))
                    }
                }
            }
            task.resume()
        }
    }

    func setupMainMenu() {
        let mainMenu = NSMenu()

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
        let localVersion = getCurrentVersion(targetDir: targetDir)

        guard let url = URL(string: "https://raw.githubusercontent.com/ssayoglu/uyap-dilekce-hazirlayici/main/version.json?t=\(Date().timeIntervalSince1970)") else { return }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalAndRemoteCacheData
        request.timeoutInterval = 6.0

        let task = URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            guard let self = self else { return }
            
            DispatchQueue.main.async {
                guard let data = data, error == nil,
                      let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                      let remoteVersion = json["version"] as? String else {
                    let alert = NSAlert()
                    alert.messageText = "Güncelleme Kontrolü"
                    alert.informativeText = "Güncelleme sunucusuna bağlanılamadı. Lütfen internet bağlantınızı kontrol ediniz."
                    alert.alertStyle = .warning
                    alert.runModal()
                    return
                }

                let changelogItems = json["changelog"] as? [String] ?? []
                let changelogText = changelogItems.isEmpty ? "" : "\n\n📋 Yeni Sürüm Notları:\n• " + changelogItems.joined(separator: "\n• ")

                if self.isVersion(remoteVersion, greaterThan: localVersion) {
                    self.performFullUpdate(targetDir: targetDir, remoteVersion: remoteVersion, changelogText: changelogText)
                } else {
                    let alert = NSAlert()
                    alert.messageText = "Sürüm Güncel"
                    alert.informativeText = "Uygulamanız güncel (v\(localVersion)).\nEn son sürümü kullanıyorsunuz.\(changelogText)"
                    alert.alertStyle = .informational
                    alert.runModal()
                }
            }
        }
        task.resume()
    }

    func performFullUpdate(targetDir: String, remoteVersion: String, changelogText: String) {
        let updateTask = Process()
        updateTask.launchPath = "/bin/bash"
        updateTask.arguments = ["-c", "curl -fsSL https://raw.githubusercontent.com/ssayoglu/uyap-dilekce-hazirlayici/main/update.sh | bash -s -- --in-app"]
        try? updateTask.run()
        updateTask.waitUntilExit()

        self.startPythonServer(targetDir: targetDir)

        DispatchQueue.main.asyncAfter(deadline: .now() + 0.6) {
            self.loadWebPage()
            let alert = NSAlert()
            alert.messageText = "Güncelleme Başarılı"
            alert.informativeText = "Uygulama başarıyla v\(remoteVersion) sürümüne güncellendi!\(changelogText)"
            alert.alertStyle = .informational
            alert.runModal()
        }
    }

    func setupStatusItem() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        if let button = statusItem?.button {
            button.title = "⚖️"
            button.target = self
            button.action = #selector(togglePopover(_:))
            button.sendAction(on: [.leftMouseUp, .rightMouseUp])
        }

        // Setup NSPopover for fast Mazeret workflow
        let popover = NSPopover()
        popover.contentSize = NSSize(width: 360, height: 480)
        popover.behavior = .transient
        popover.animates = true

        let popoverVC = NSViewController()
        let pWebView = WKWebView(frame: NSRect(x: 0, y: 0, width: 360, height: 480))
        popoverVC.view = pWebView
        popover.contentViewController = popoverVC

        self.popover = popover
        self.popoverWebView = pWebView
    }

    @objc func togglePopover(_ sender: AnyObject?) {
        guard let button = statusItem?.button else { return }

        let currentEvent = NSApp.currentEvent
        if currentEvent?.type == .rightMouseUp {
            // Right click opens main app window
            showAppWindow()
            return
        }

        if let popover = self.popover {
            if popover.isShown {
                popover.performClose(sender)
            } else {
                if let url = URL(string: "http://127.0.0.1:5678/mazeret") {
                    let req = URLRequest(url: url)
                    self.popoverWebView?.load(req)
                }
                popover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY)
            }
        }
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
