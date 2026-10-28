using System;
using System.Collections;
using System.IO;
using System.Reflection;

class Probe4
{
    static string DwsimDir = @"C:\Users\Lenovo\AppData\Local\DWSIM";
    static Assembly Resolve(object sender, ResolveEventArgs args)
    {
        var name = new AssemblyName(args.Name).Name + ".dll";
        foreach (var dir in new[] { DwsimDir, Path.Combine(DwsimDir, "ThermoCS"),
            Path.Combine(DwsimDir, "Lib"), Path.Combine(DwsimDir, "runtimes") })
        {
            var path = Path.Combine(dir, name);
            if (File.Exists(path)) return Assembly.LoadFrom(path);
        }
        return null;
    }

    static void Main(string[] args)
    {
        AppDomain.CurrentDomain.AssemblyResolve += Resolve;
        var temp = @"C:\Users\Lenovo\Desktop\ChemELlm\data\qa\dwsim-temp";
        Directory.CreateDirectory(temp);
        Environment.SetEnvironmentVariable("TEMP", temp);
        Environment.SetEnvironmentVariable("TMP", temp);
        Directory.SetCurrentDirectory(DwsimDir);
        var asm = Assembly.LoadFrom(Path.Combine(DwsimDir, "DWSIM.Automation.dll"));
        var type = asm.GetType("DWSIM.Automation.Automation3");
        var automation = Activator.CreateInstance(type);
        var load = type.GetMethod("LoadFlowsheet", new[] { typeof(string) });
        object sim = load.Invoke(automation, new object[] { args[0] });
        var calc = type.GetMethod("CalculateFlowsheet", new[] { sim.GetType().GetInterfaces()[0], typeof(object) });
        if (calc == null) { foreach (var m in type.GetMethods()) if (m.Name == "CalculateFlowsheet" && m.GetParameters().Length == 2) calc = m; }
        calc.Invoke(automation, new object[] { sim, null });
        var objects = (IDictionary)sim.GetType().GetProperty("SimulationObjects").GetValue(sim, null);
        foreach (DictionaryEntry entry in objects)
        {
            var obj = entry.Value;
            if (!obj.GetType().Name.Contains("MaterialStream")) continue;
            Console.WriteLine("STREAM " + obj.GetType().FullName);
            foreach (var m in obj.GetType().GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            {
                if (m.GetParameters().Length == 0 && (m.Name.StartsWith("Get") || m.Name.StartsWith("get_")))
                    Console.WriteLine("  M " + m.ReturnType.Name + " " + m.Name);
            }
            break;
        }
    }
}
