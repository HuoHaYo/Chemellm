using System;
using System.Collections;
using System.IO;
using System.Reflection;

class Probe5
{
    static string DwsimDir = @"C:\Users\Lenovo\AppData\Local\DWSIM";
    static Assembly Resolve(object sender, ResolveEventArgs args)
    {
        var name = new AssemblyName(args.Name).Name + ".dll";
        foreach (var dir in new[] { DwsimDir, Path.Combine(DwsimDir, "ThermoCS"), Path.Combine(DwsimDir, "Lib") })
        { var p = Path.Combine(dir, name); if (File.Exists(p)) return Assembly.LoadFrom(p); }
        return null;
    }
    static void Main(string[] args)
    {
        AppDomain.CurrentDomain.AssemblyResolve += Resolve;
        var temp = @"C:\Users\Lenovo\Desktop\ChemELlm\data\qa\dwsim-temp";
        Directory.CreateDirectory(temp);
        Environment.SetEnvironmentVariable("TEMP", temp); Environment.SetEnvironmentVariable("TMP", temp);
        Directory.SetCurrentDirectory(DwsimDir);
        var asm = Assembly.LoadFrom(Path.Combine(DwsimDir, "DWSIM.Automation.dll"));
        var type = asm.GetType("DWSIM.Automation.Automation3");
        var auto = Activator.CreateInstance(type);
        object sim = type.GetMethod("LoadFlowsheet", new[] { typeof(string) }).Invoke(auto, new object[] { args[0] });
        var dict = (IDictionary)sim.GetType().GetProperty("SimulationObjects").GetValue(sim, null);
        foreach (DictionaryEntry e in dict)
        {
            var o = e.Value;
            var g = o.GetType().GetProperty("GraphicObject").GetValue(o, null);
            if (g == null) continue;
            Console.WriteLine("OBJ " + o.GetType().Name + " GRAPHIC " + g.GetType().FullName);
            foreach (var p in g.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance))
                Console.WriteLine("  P " + p.Name + " = " + p.GetValue(g, null));
            foreach (var m in g.GetType().GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly))
                if (m.GetParameters().Length == 0) Console.WriteLine("  M " + m.ReturnType.Name + " " + m.Name);
            break;
        }
    }
}
