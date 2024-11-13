using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.Diagnostics;
public class RunPy : MonoBehaviour
{
    void Start()
    {
        UnityEngine.Debug.Log("Hello world!");
    }
    void Update()
    {

        if (Input.GetKeyDown(KeyCode.R))
        {
            try {
                Process psi = new Process();
                UnityEngine.Debug.Log("ProcessLaunched");
                psi.StartInfo.FileName = "C:\\ProgramData\\anaconda3\\python.exe";
                // 시작할 어플리케이션 또는 문서
                UnityEngine.Debug.Log("PythonLaunched");
                psi.StartInfo.Arguments = "C:\\Users\\2011j\\EE101\\4_4_1_for_c#.py";
                // 애플 시작시 사용할 인수
                UnityEngine.Debug.Log("ProjLaunched");
                psi.StartInfo.CreateNoWindow = false;
                psi.StartInfo.RedirectStandardOutput = true;
                // 새창 안띄울지
                psi.StartInfo.UseShellExecute = false;
                // 프로세스를 시작할때 운영체제 셸을 사용할지
                psi.Start();     
                   
                while (!psi.StandardOutput.EndOfStream)
                {
                    UnityEngine.Debug.Log("실행중");
                    string line = psi.StandardOutput.ReadLine();
                    // do something with line
                    UnityEngine.Debug.Log(line);
                }
                UnityEngine.Debug.Log("실행");
            }
            catch(Exception e)
            {
                UnityEngine.Debug.LogError("Unable to launch app: " + e.Message);
            }
        }
    }
}
