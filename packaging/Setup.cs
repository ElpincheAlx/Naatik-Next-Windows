using System;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Diagnostics;
using System.ComponentModel;
using System.Collections.Generic;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using System.Drawing;
[assembly: AssemblyTitle("Naatik Next Setup")]
[assembly: AssemblyVersion("1.0.0.0")]
[assembly: AssemblyFileVersion("1.0.0.0")]
class Setup : Form {
    TextBox log = new TextBox(); Button install = new Button(); ProgressBar bar = new ProgressBar();
    ComboBox languages = new ComboBox(); Label description = new Label(); bool busy;
    string code = "es";
    Dictionary<string, string> catalog;
    string target = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "NaatikNext", "1.0");
    static string Profile() {
        string profile = Environment.GetEnvironmentVariable("NAATIK_WINDOWS_PROFILE");
        return String.IsNullOrEmpty(profile) ? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "NaatikNextWindows") : profile;
    }
    static string ExistingLanguage() {
        string config = Path.Combine(Profile(), "config");
        string path = Path.Combine(config, "ui-language.txt");
        if(File.Exists(path)) {
            string value = File.ReadAllText(path).Trim();
            if(value == "es" || value == "en") return value;
        }
        return File.Exists(Path.Combine(config, "settings.json")) ? "es" : null;
    }
    void LoadLanguage(string language) {
        code = language;
        using(var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(language+".json"))
        using(var reader = new StreamReader(stream)) catalog = new JavaScriptSerializer().Deserialize<Dictionary<string,string>>(reader.ReadToEnd());
        Text = T("setup.title");
        description.Text = T("setup.description") + target;
        install.Text = T("setup.install");
    }
    string T(string key) { return catalog[key]; }
    Setup() {
        Width=820; Height=580; MinimumSize=new Size(720,520); StartPosition=FormStartPosition.CenterScreen;
        var languagePanel = new FlowLayoutPanel { Dock=DockStyle.Top, Height=70, Padding=new Padding(12), WrapContents=false };
        languagePanel.Controls.Add(new Label { Text="Idioma / Language", AutoSize=true, Margin=new Padding(0,7,12,0) });
        languages.DropDownStyle=ComboBoxStyle.DropDownList; languages.Width=220;
        languages.Items.AddRange(new object[]{"Español", "English"});
        languagePanel.Controls.Add(languages);
        description.Dock=DockStyle.Top; description.Height=145; description.Padding=new Padding(12);
        install.Dock=DockStyle.Bottom; install.Height=48; install.Enabled=false;
        bar.Dock=DockStyle.Bottom; bar.Height=22;
        log.Multiline=true; log.ReadOnly=true; log.ScrollBars=ScrollBars.Vertical; log.Dock=DockStyle.Fill;
        Controls.Add(log); Controls.Add(bar); Controls.Add(install); Controls.Add(description); Controls.Add(languagePanel);
        LoadLanguage("es");
        Text="Na’atik Next 1.0 — Español / English";
        description.Text="Elige Español o English y pulsa Instalar.\r\nChoose Español or English, then click Install.\r\n\r\nNo se descargará ni instalará nada antes.\r\nNothing is downloaded or installed before you click Install.";
        install.Text="Instalar / Install";
        languages.SelectedIndexChanged += delegate {
            if(languages.SelectedIndex<0) return;
            LoadLanguage(languages.SelectedIndex==0 ? "es" : "en"); install.Enabled=true;
        };
        try {
            string existing=ExistingLanguage();
            if(existing!=null) languages.SelectedIndex=existing=="es" ? 0 : 1;
        } catch(Exception error) { log.Text=T("setup.read_error")+error.Message; }
        install.Click += delegate { if(languages.SelectedIndex>=0) Run(); };
        FormClosing += delegate(object sender,FormClosingEventArgs e) {
            if(busy) { e.Cancel=true; MessageBox.Show(T("setup.wait"),Text); }
        };
    }
    void Line(string text) { if(text!=null && !IsDisposed) BeginInvoke((Action)(()=>log.AppendText(text+Environment.NewLine))); }
    static void Extract(string destination) {
        Directory.CreateDirectory(destination);
        string root=Path.GetFullPath(destination).TrimEnd(Path.DirectorySeparatorChar)+Path.DirectorySeparatorChar;
        using(var stream=Assembly.GetExecutingAssembly().GetManifestResourceStream("payload.zip"))
        using(var zip=new ZipArchive(stream,ZipArchiveMode.Read)) {
            foreach(var entry in zip.Entries) {
                const string prefix="Naatik-next-windows/";
                if(!entry.FullName.StartsWith(prefix,StringComparison.Ordinal)) throw new Exception("setup.bad_entry");
                string relative=entry.FullName.Substring(prefix.Length).Replace('/',Path.DirectorySeparatorChar);
                string path=Path.GetFullPath(Path.Combine(root,relative));
                if(!path.StartsWith(root,StringComparison.OrdinalIgnoreCase)) throw new Exception("setup.bad_path");
                if(entry.FullName.EndsWith("/")) {Directory.CreateDirectory(path);continue;}
                Directory.CreateDirectory(Path.GetDirectoryName(path));
                using(var input=entry.Open()) using(var output=File.Create(path)) input.CopyTo(output);
            }
        }
    }
    void Run() {
        busy=true; install.Enabled=false; languages.Enabled=false; bar.Style=ProgressBarStyle.Marquee; log.Clear();
        var worker=new BackgroundWorker();
        worker.DoWork += delegate {
            if(!Environment.Is64BitOperatingSystem) throw new Exception(T("setup.x64"));
            Line(T("setup.extract"));
            try { Extract(target); } catch(Exception e) { throw new Exception(T("setup.extract_error")+(catalog.ContainsKey(e.Message) ? T(e.Message) : e.Message)); }
            Line(T("setup.external"));
            var info=new ProcessStartInfo("powershell.exe", "-NoProfile -ExecutionPolicy Bypass -File \""+Path.Combine(target,"packaging","install-user.ps1")+"\"");
            info.UseShellExecute=false; info.CreateNoWindow=true; info.RedirectStandardOutput=true; info.RedirectStandardError=true;
            info.StandardOutputEncoding=System.Text.Encoding.UTF8; info.StandardErrorEncoding=System.Text.Encoding.UTF8;
            info.EnvironmentVariables["NAATIK_UI_LANGUAGE"]=code;
            info.WorkingDirectory=target;
            using(var process=new Process()) {
                process.StartInfo=info;
                process.OutputDataReceived += (s,e)=>Line(e.Data); process.ErrorDataReceived += (s,e)=>Line(e.Data);
                process.Start(); process.BeginOutputReadLine(); process.BeginErrorReadLine(); process.WaitForExit();
                if(process.ExitCode!=0) throw new Exception(T("setup.failed")+Path.Combine(target,"install.log"));
            }
        };
        worker.RunWorkerCompleted += (s,e)=> {
            busy=false; install.Enabled=true; languages.Enabled=true; bar.Style=ProgressBarStyle.Blocks; bar.Value=e.Error==null?100:0;
            if(e.Error!=null) { string message=T("setup.error_details")+e.Error.Message; Line(message);MessageBox.Show(message,T("setup.error")); }
            else { Line(T("setup.done")); MessageBox.Show(T("setup.done"),Text); }
        };
        worker.RunWorkerAsync();
    }
    [STAThread] static int Main(string[] args) {
        if(args.Length==2 && args[0]=="--extract") {try {Extract(args[1]);return 0;} catch{return 1;}}
        Application.EnableVisualStyles(); Application.Run(new Setup()); return 0;
    }
}
