using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.Diagnostics;
public class RunPy : MonoBehaviour
{
    void Start()
    {
        try {
            Process psi = new Process();
            UnityEngine.Debug.Log("ProcessLaunched");
            psi.StartInfo.FileName = @"C:\\Users\\USERPC\\AppData\\Local\\Programs\\Python\\Python312\\python.exe";
            // 시작할 어플리케이션 또는 문서
            UnityEngine.Debug.Log("PythonLaunched");
            psi.StartInfo.Arguments = @"C:\Users\USERPC\EE101\\4.4.1_for_c#.py";
            // 애플 시작시 사용할 인수
            UnityEngine.Debug.Log("ProjLaunched");
            psi.StartInfo.CreateNoWindow = false;
            // 새창 안띄울지
            psi.StartInfo.RedirectStandardOutput = true;
            // python.exe에서 출력되는 standardoutput을 redirection
            psi.StartInfo.UseShellExecute = false;
            // 프로세스를 시작할때 운영체제 셸을 사용할지
            psi.Start();     
                
            while (!psi.StandardOutput.EndOfStream)
            {
                string line = psi.StandardOutput.ReadLine(); 
                //python.exe에서 나온 output을 읽어서 출력
                UnityEngine.Debug.Log(line);
            }
        }
        catch(Exception e)
        {
            UnityEngine.Debug.LogError("Unable to launch app: " + e.Message);
        }

    }
    void Update()
    {
        
    }
}
