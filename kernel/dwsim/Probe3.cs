using System;
using System.Collections;
using System.IO;
using System.Reflection;

class Probe3
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
        try
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
            Console.WriteLine("SIM " + sim.GetType().FullName);
            foreach (var p in sim.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance))
                if (p.Name == "Solved" || p.Name == "ErrorMessage") Console.WriteLine("STATE " + p.Name + "=" + p.GetValue(sim, null));

            MethodInfo calc = null;
            foreach (var m in type.GetMethods()) if (m.Name == "CalculateFlowsheet" && m.GetParameters().Length == 2) calc = m;
            Console.WriteLine("CALC " + calc);
            try { calc.Invoke(automation, new object[] { sim, null }); } catch (Exception ex) { Console.WriteLine("CALCERR " + (ex.InnerException != null ? ex.InnerException.Message : ex.Message)); }
            foreach (var p in sim.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance))
                if (p.Name == "Solved" || p.Name == "ErrorMessage") Console.WriteLine("POST " + p.Name + "=" + p.GetValue(sim, null));

            var objects = (IDictionary)sim.GetType().GetProperty("SimulationObjects").GetValue(sim, null);
            Console.WriteLine("COUNT " + objects.Count);
            foreach (DictionaryEntry entry in objects)
            {
                var obj = entry.Value;
                Console.WriteLine("OBJ " + obj.GetType().Name + " " + entry.Key);
                if (obj.GetType().Name.Contains("MaterialStream"))
                {
                    foreach (var p in obj.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance))
                    {
                        var value = p.GetValue(obj, null);
                        var array = value as Array;
                        Console.WriteLine("  " + p.Name + " = " + (array != null ? "array[" + array.Length + "]" : (value ?? "null")));
                    }
                }
                else if (obj.GetType().Name.Contains("Reactor"))
                {
                    foreach (var p in obj.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance))
                        if (p.Name.Contains("Delta") || p.Name.Contains("Temperature") || p.Name.Contains("Flow") || p.Name.Contains("Heat"))
                            Console.WriteLine("  UO " + p.Name + " = " + p.GetValue(obj, null));
                }
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine("ERR " + ex.GetType().FullName + ": " + ex.Message);
            if (ex.InnerException != null) Console.WriteLine(ex.InnerException.ToString());
        }
    }
}



