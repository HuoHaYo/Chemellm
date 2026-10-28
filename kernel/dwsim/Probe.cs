using System;
using System.IO;
using System.Reflection;

class Probe
{
    static void Main(string[] args)
    {
        string dir = args.Length > 0 ? args[0] : @"C:\Users\Lenovo\AppData\Local\DWSIM";
        Directory.SetCurrentDirectory(dir);
        var asm = Assembly.LoadFrom(Path.Combine(dir, "DWSIM.Automation.dll"));
        foreach (var t in asm.GetTypes())
        {
            if (t.FullName.Contains("Automation"))
            {
                Console.WriteLine("TYPE " + t.FullName);
                foreach (var c in t.GetConstructors())
                    Console.WriteLine("  CTOR " + c);
                foreach (var m in t.GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly))
                    Console.WriteLine("  M " + m);
            }
        }
    }
}
