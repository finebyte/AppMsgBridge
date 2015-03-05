package test.appmsgbridge;

import java.text.Normalizer;
import java.text.Normalizer.Form;
import java.util.UUID;
import test.appmsgbridge.R;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.util.Log;
import android.view.Menu;
import android.view.View;
import android.widget.TextView;
import android.widget.Toast;

@SuppressLint("NewApi")
public class MainActivity extends Activity {

	final static String TAG="AppMsgBridge";
	
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_main);

		DebugRcvr d = new DebugRcvr();
		registerReceiver(d, new IntentFilter("com.getpebble.action.app.SEND"));
		registerReceiver(d, new IntentFilter("com.getpebble.action.app.ACK"));
		registerReceiver(d, new IntentFilter("com.getpebble.action.app.NACK"));
		registerReceiver(d, new IntentFilter("com.getpebble.action.app.RECEIVE_ACK"));
		registerReceiver(d, new IntentFilter("com.getpebble.action.app.RECEIVE_NACK"));
		registerReceiver(d, new IntentFilter("com.getpebble.action.ACK"));
		registerReceiver(d, new IntentFilter("com.getpebble.action.NACK"));
		registerReceiver(d, new IntentFilter("com.getpebble.action.app.START"));
		registerReceiver(d, new IntentFilter("com.getpebble.action.app.STOP"));
		registerReceiver(d, new IntentFilter("com.getpebble.action.app.CONFIGURE"));
		registerReceiver(d, new IntentFilter("com.getpebble.action.app.RECEIVE"));


		SharedPreferences mySP=PreferenceManager.getDefaultSharedPreferences(this);

		String uuid = mySP.getString("uuid", "");		
		TextView uuidtv = (TextView)findViewById(R.id.UUIDEditor);
		uuidtv.setText(uuid);

		String msg = mySP.getString("msg","");
		TextView dgEdit=(TextView)findViewById(R.id.MsgEditor);
		dgEdit.setText(msg);

		String wsuri = mySP.getString("wsuri", "ws://192.168.0.6:9000");
		TextView wsedit = (TextView)findViewById(R.id.editText_wsuri);
		wsedit.setText(wsuri);
	}

	public void doEditTextClick(View view) {
		Toast.makeText(getBaseContext(), "Enter a Pebble App UUID", Toast.LENGTH_SHORT).show();

	}

	public void doMsgTextClick(View view) {
		Toast.makeText(getBaseContext(), "Enter a Pebble AppMessage in Android Json Format", Toast.LENGTH_SHORT).show();

	}



	int count = 0;
	public void sendDataGram(View view) {

		final Intent i = new Intent("com.getpebble.action.app.SEND");
		TextView uuidtv = (TextView)findViewById(R.id.UUIDEditor);
		String uuids=uuidtv.getText().toString();	
		if (uuids==null || uuids.isEmpty()) {
			Toast.makeText(getBaseContext(), "Enter a Pebble App UUID", Toast.LENGTH_SHORT).show();

		} else {
			UUID myUUID = UUID.fromString(uuids);
			i.putExtra("uuid", myUUID);
			i.putExtra("transaction_id",150);
			TextView dgEdit=(TextView)findViewById(R.id.MsgEditor);
			String msgData=dgEdit.getText().toString();
			i.putExtra("msg_data", msgData);
			sendBroadcast(i);
			Log.d(TAG,"Sent SEND to "+myUUID.toString() +"\n" + msgData);

			SharedPreferences mySP=PreferenceManager.getDefaultSharedPreferences(this);
			mySP.edit().putString("uuid", uuids).apply();
			mySP.edit().putString("msg", msgData).apply();
		}


	}

	public void sendStart(View view) {
		final Intent i = new Intent("com.getpebble.action.app.START");
		// cf1e816a-9db0-4511-bbb8-f60c48ca8fac
		TextView uuidtv = (TextView)findViewById(R.id.UUIDEditor);
		String uuids=uuidtv.getText().toString();
		if (uuids==null || uuids.isEmpty()) {
			Toast.makeText(getBaseContext(), "Enter a Pebble App UUID", Toast.LENGTH_SHORT).show();

		} else {

			UUID myUUID = UUID.fromString(uuids);
			i.putExtra("uuid", myUUID);
			sendBroadcast(i);
			Log.d(TAG,"Sent START to "+myUUID.toString());
			SharedPreferences mySP=PreferenceManager.getDefaultSharedPreferences(this);
			mySP.edit().putString("uuid", uuids).apply();
		}
	}

	public void sendStartBridge(View view) {

		TextView wsuri_tv = (TextView)findViewById(R.id.editText_wsuri);
		String wsuri=wsuri_tv.getText().toString();		

		if (!wsuri.isEmpty()) {

			wsuri=wsuri.toLowerCase();
			Intent startIntent = new Intent(MainActivity.this, ForegroundService.class);
			startIntent.setAction(Constants.ACTION.STARTFOREGROUND_ACTION);
			startIntent.putExtra("wsuri", wsuri);
			startService(startIntent);

			SharedPreferences mySP=PreferenceManager.getDefaultSharedPreferences(this);
			mySP.edit().putString("wsuri", wsuri).apply();
		} else {
			Toast.makeText(getBaseContext(), "Please enter a valid wsuri for the other half of the bridge", Toast.LENGTH_SHORT).show();

		}
	}

	public void sendStopBridge(View view) {

		Intent startIntent = new Intent(MainActivity.this, ForegroundService.class);
		startIntent.setAction(Constants.ACTION.STOPFOREGROUND_ACTION);
		startService(startIntent);
	}



}
