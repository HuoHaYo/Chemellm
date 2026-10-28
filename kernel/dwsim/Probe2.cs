using System;
using System.Collections;
using System.IO;
using System.Reflection;

class Probe2
{
    static string DwsimDir = @"C:\Users\Lenovo\AppData\Local\DWSIM";
    static Assembly Resolve(object sender, ResolveEventArgs args)
    {
        var name = new AssemblyName(args.Name).Name + ".dll";
        foreach (var dir in new[] { DwsimDir,
            Path.Combine(DwsimDir, "ThermoCS"), Path.Combine(DwsimDir, "Lib"),
            Path.Combine(DwsimDir, "runtimes"), Path.Combine(DwsimDir, "extenders") })
        {
            var path = Path.Combine(dir, name);
            if (File.Exists(path)) return Assembly.LoadFrom(path);
        }
        return null;
    }

    static void Main(string[] args)
    {
        try
        {
            AppDomain.CurrentDomain.AssemblyResolve += Resolve;
            Directory.SetCurrentDirectory(DwsimDir);
            var asm = Assembly.LoadFrom(Path.Combine(DwsimDir, "DWSIM.Automation.dll"));
            var type = asm.GetType("DWSIM.Automation.Automation3");
            var automation = Activator.CreateInstance(type);
            var load = type.GetMethod("LoadFlowsheet", new[] { typeof(string) });
            object sim = load.Invoke(automation, new object[] { args[0] });
            Console.WriteLine("SIM TYPE " + sim.GetType().FullName);
            object objects = sim.GetType().GetProperty("SimulationObjects").GetValue(sim, null);
            Console.WriteLine("COUNT " + ((IDictionary)objects).Count);
            int n = 0;
            foreach (DictionaryEntry entry in (IDictionary)objects)
            {
                var obj = entry.Value;
                Console.WriteLine("OBJ " + entry.Key + " | " + obj.GetType().FullName);
                n++;
                if (n >= 3) break;
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine("ERR " + ex.GetType().FullName + ": " + ex.Message);
            if (ex.InnerException != null) Console.WriteLine(ex.InnerException.ToString());
        }
    }
}

