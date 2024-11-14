using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

public class FlaskConnectionTester : MonoBehaviour
{
    private string flaskUrl1 = "http://192.168.247.150:5000/get_graph1";  // 첫 번째 이미지 URL
    private string flaskUrl2 = "http://192.168.247.150:5000/get_graph2";  // 두 번째 이미지 URL

    void Start()
    {
        StartCoroutine(GetImagesFromServer());
    }

    IEnumerator GetImagesFromServer()
    {
        // 첫 번째 이미지 요청
        UnityWebRequest www1 = UnityWebRequestTexture.GetTexture(flaskUrl1);
        yield return www1.SendWebRequest();

        if (www1.result != UnityWebRequest.Result.Success)
        {
            Debug.Log("Failed to connect to server for image 1: " + www1.error);
        }
        else
        {
            Texture2D texture1 = DownloadHandlerTexture.GetContent(www1);
            Debug.Log("Image 1 received from server");

            // 첫 번째 이미지 Quad 생성 및 텍스처 적용
            GameObject quad1 = GameObject.CreatePrimitive(PrimitiveType.Quad);
            quad1.transform.position = new Vector3(-1.5f, 0, 5);  // 왼쪽 위치 설정
            quad1.GetComponent<Renderer>().material.mainTexture = texture1;
        }

        // 두 번째 이미지 요청
        UnityWebRequest www2 = UnityWebRequestTexture.GetTexture(flaskUrl2);
        yield return www2.SendWebRequest();

        if (www2.result != UnityWebRequest.Result.Success)
        {
            Debug.Log("Failed to connect to server for image 2: " + www2.error);
        }
        else
        {
            Texture2D texture2 = DownloadHandlerTexture.GetContent(www2);
            Debug.Log("Image 2 received from server");

            // 두 번째 이미지 Quad 생성 및 텍스처 적용
            GameObject quad2 = GameObject.CreatePrimitive(PrimitiveType.Quad);
            quad2.transform.position = new Vector3(1.5f, 0, 5);  // 오른쪽 위치 설정
            quad2.GetComponent<Renderer>().material.mainTexture = texture2;
        }
    }
}
