package org.cocos2dx.cpp;

import android.app.AlertDialog;
import android.graphics.Color;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.*;
import org.cocos2dx.lib.Cocos2dxActivity;

/** Standalone developer overlay; every game operation is queued on the GL thread. */
public final class DevMenu {
    private static native int nativeApply(int command, int a, int b, int c, int d);
    private static String loadError;
    static {
        try { System.loadLibrary("HatchimonDev"); }
        catch (Throwable e) { loadError = e.toString(); }
    }

    public static void install(final Cocos2dxActivity activity) {
        Button button = new Button(activity);
        button.setText("DEV");
        button.setTextColor(Color.WHITE);
        button.setBackgroundColor(0xCC284C73);
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(dp(activity,72),dp(activity,44));
        lp.gravity = Gravity.TOP | Gravity.RIGHT;
        lp.topMargin = dp(activity,48);
        activity.addContentView(button, lp);
        button.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { show(activity); }
        });
    }
    private static int dp(Cocos2dxActivity a, int v) {
        return (int)(a.getResources().getDisplayMetrics().density*v+0.5f);
    }
    private static void label(Cocos2dxActivity a, LinearLayout l, String s) {
        TextView t = new TextView(a); t.setText(s); t.setTextSize(16);
        t.setPadding(0,dp(a,10),0,dp(a,4)); l.addView(t);
    }
    private static Spinner select(Cocos2dxActivity a, LinearLayout l, String[] items) {
        Spinner s = new Spinner(a);
        ArrayAdapter<String> adapter = new ArrayAdapter<String>(a,android.R.layout.simple_spinner_item,items);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        s.setAdapter(adapter); l.addView(s); return s;
    }
    private static EditText number(Cocos2dxActivity a, LinearLayout l, String value) {
        EditText e = new EditText(a); e.setInputType(InputType.TYPE_CLASS_NUMBER);
        e.setSingleLine(true); e.setText(value); l.addView(e); return e;
    }
    private static int parse(EditText e, int min, int max) {
        try { long n = Long.parseLong(e.getText().toString().trim());
            if(n>=min && n<=max) return (int)n;
        } catch (NumberFormatException ignored) { }
        return -1;
    }
    private static void toast(Cocos2dxActivity a,String s) { Toast.makeText(a,s,Toast.LENGTH_LONG).show(); }
    private static void apply(final Cocos2dxActivity a,final int command,final int x,final int y,final int z,final int w) {
        if(loadError != null) { toast(a,"Не удалось загрузить мод: "+loadError); return; }
        a.runOnGLThread(new Runnable() { public void run() {
            final int result = nativeApply(command,x,y,z,w);
            a.runOnUiThread(new Runnable() { public void run() {
                if(result>=0) toast(a,command==2 ? "Выдано хачимонов: "+result : "Валюта начислена и сохранена");
                else if(result==-2) toast(a,"Сначала откройте ферму и завершите обучение");
                else if(result==-3) toast(a,"На ферме нет свободных мест");
                else if(result==-4) toast(a,"Недопустимые параметры");
                else toast(a,"Не найдены функции игры (код "+result+")");
            }});
        }});
    }
    private static void show(final Cocos2dxActivity a) {
        ScrollView scroll = new ScrollView(a);
        LinearLayout content = new LinearLayout(a); content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(a,20),dp(a,6),dp(a,20),dp(a,12)); scroll.addView(content);
        label(a,content,"Откройте ферму после обучения. Изменения сохраняются автоматически.");
        label(a,content,"Валюта");
        final Spinner currency = select(a,content,new String[]{"Золото","Кристаллы (Cash)","Рубины"});
        label(a,content,"Сумма (1–1 000 000 000), предел баланса 2 миллиарда");
        final EditText amount = number(a,content,"10000");
        Button grant = new Button(a); grant.setText("Начислить валюту"); content.addView(grant);
        label(a,content,"Уровень хачимона (1–72)");
        final EditText level = number(a,content,"37");
        label(a,content,"37–72: светящиеся хачимоны. Доступны все уровни этой версии игры.");
        label(a,content,"Тип");
        final Spinner type = select(a,content,new String[]{"Случайный","Тип 1","Тип 2","Тип 3","Тип 4"});
        label(a,content,"Количество (1–10)");
        final EditText count = number(a,content,"1");
        Button spawn = new Button(a); spawn.setText("Выдать хачимонов"); content.addView(spawn);
        final AlertDialog dialog = new AlertDialog.Builder(a).setTitle("Merge Hatchimon · Developer")
            .setView(scroll).setNegativeButton("Закрыть",null).create();
        grant.setOnClickListener(new View.OnClickListener() { public void onClick(View v) {
            int n=parse(amount,1,1000000000);
            if(n<0) { toast(a,"Введите сумму от 1 до 1 000 000 000"); return; }
            int kind=currency.getSelectedItemPosition(); dialog.dismiss(); apply(a,1,kind,n,0,0);
        }});
        spawn.setOnClickListener(new View.OnClickListener() { public void onClick(View v) {
            int n=parse(count,1,10);
            if(n<0) { toast(a,"Введите количество от 1 до 10"); return; }
            int wanted=parse(level,1,72);
            if(wanted<0) { toast(a,"Введите уровень от 1 до 72"); return; }
            int tier=(wanted-1)/3, variant=(wanted-1)%3, kind=type.getSelectedItemPosition()-1;
            dialog.dismiss(); apply(a,2,tier,variant,kind,n);
        }});
        dialog.show();
    }
}
