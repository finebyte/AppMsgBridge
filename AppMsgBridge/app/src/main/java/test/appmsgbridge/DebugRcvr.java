package test.appmsgbridge;

import java.util.UUID;

import org.json.*;

import android.annotation.SuppressLint;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;

public class DebugRcvr extends BroadcastReceiver{

	static final String TAG="BridgeRcvr";
	
	@SuppressLint("NewApi")
	@Override
	public void onReceive(Context context, Intent intent) {
		Log.d(TAG,"DEBUG DebugRcvr Got intent " + intent);

		if (intent.getAction().equals("com.getpebble.action.app.SEND")) {
			try {
				Bundle bundle = intent.getExtras();
				Integer txid = bundle.getInt("transaction_id");
				UUID uuid = (UUID)bundle.getSerializable("uuid");
				String msg_data = bundle.getString("msg_data");
				JSONArray jsa_msg_data = new JSONArray(msg_data);
				JSONObject jso = new JSONObject();
				jso.put("uuid", uuid);
				jso.put("txid",""+txid);
				jso.put("msg_data",jsa_msg_data);
				Log.d(TAG,"Sending " + jso.toString());
				sendWS(context, jso.toString());

			} catch (Exception ex) {
				ex.printStackTrace();
			}
		}

		if (intent.getAction().equals("com.getpebble.action.app.ACK")) {
			try {
				Bundle bundle = intent.getExtras();
				Integer txid = bundle.getInt("transaction_id");
				JSONObject jso = new JSONObject();
				jso.put("txid",""+txid);
				jso.put("acknack", "ack");
				Log.d(TAG,"Sending " + jso.toString());
				sendWS(context, jso.toString());

			} catch (Exception ex) {
				ex.printStackTrace();
			}

		}

		if (intent.getAction().equals("com.getpebble.action.app.NACK")) {
			try {
				Bundle bundle = intent.getExtras();
				Integer txid = bundle.getInt("transaction_id");
				JSONObject jso = new JSONObject();
				jso.put("txid",""+txid);
				jso.put("acknack", "nack");
				Log.d(TAG,"Sending " + jso.toString());
				sendWS(context, jso.toString());
			} catch (Exception ex) {
				ex.printStackTrace();
			}

		}

		// Log any of the Pebble Intents so we can see what is going on
		
		Bundle bundle = intent.getExtras();
		if (bundle==null) {
			Log.d(TAG,"DebugRcvr no extras?!?");
		} else {
			for (String key : bundle.keySet()) {
				Object value = bundle.get(key);
				Uri u = intent.getData();
				Log.d(TAG, String.format("%s %s (%s)", key,  
						value.toString(), value.getClass().getName()));
				if (u!=null) {
					Log.d(TAG,"Intent data uri=" + u);
				}
				//intent.getData();
				if (value.getClass().getName().equals("android.graphics.Bitmap")) {
					android.graphics.Bitmap b = (android.graphics.Bitmap)value;
					Log.d(TAG,"Bitmap size="+b.getByteCount());
				}

			}
		}
	}
	
	public void sendWS(Context context, String msg) {
		Log.d(TAG,"DebugRcv SendWS");
		Intent startIntent = new Intent(context, ForegroundService.class);
		 startIntent.setAction(Constants.ACTION.SENDWS);
		 startIntent.putExtra("msg", msg);
		 context.startService(startIntent);

	}

}
