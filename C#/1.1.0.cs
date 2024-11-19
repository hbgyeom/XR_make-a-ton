using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

public class FlaskConnectionTester : MonoBehaviour
{
    private string flaskUrlFlag = "http://192.168.247.150:5000/get_flag";
    private string flaskUrl1 = "http://192.168.247.150:5000/get_graph1";
    private GameObject quad; // Quad 객체를 미리 선언하여 참조 유지

    void Start()
    {
        // Quad를 처음에 한 번 생성하여 초기화
        quad = GameObject.CreatePrimitive(PrimitiveType.Quad);
        quad.transform.position = new Vector3(0, 0, 5);

        StartCoroutine(CheckForUpdates());
    }

    IEnumerator CheckForUpdates()
    {
        while (true)
        {
            UnityWebRequest www = UnityWebRequest.Get(flaskUrlFlag);
            yield return www.SendWebRequest();

            if (www.result == UnityWebRequest.Result.Success)
            {
                var jsonResponse = www.downloadHandler.text;
                if (jsonResponse.Contains("\"flag\":1"))
                {
                    // flag가 1이면 이미지를 업데이트
                    StartCoroutine(UpdateTexture(flaskUrl1, "Image received from server"));
                }
            }
            else
            {
                Debug.Log("Failed to connect to server for flag check: " + www.error);
            }

            yield return new WaitForSeconds(1); // 1초마다 flag 상태 확인
        }
    }

    IEnumerator UpdateTexture(string url, string logMessage)
    {
        UnityWebRequest www = UnityWebRequestTexture.GetTexture(url);
        yield return www.SendWebRequest();

        if (www.result == UnityWebRequest.Result.Success)
        {
            Texture2D texture = DownloadHandlerTexture.GetContent(www);
            Debug.Log(logMessage);

            // quad의 텍스처만 업데이트
            quad.GetComponent<Renderer>().material.mainTexture = texture;
        }
        else
        {
            Debug.Log("Failed to connect to server for image: " + www.error);
        }
    }
}
