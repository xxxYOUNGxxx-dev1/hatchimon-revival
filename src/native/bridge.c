/* ARM32 bridge for the supplied 1.13 binary. No absolute runtime addresses. */
typedef unsigned char byte;
extern void *dlopen(const char *, int);
extern void *dlsym(void *, const char *);
static void *game;
static void *sym(const char *name) { return dlsym(game,name); }
typedef void *(*GetObject)(void);
typedef void *(*ObjectMethod)(void *);
typedef int (*CountMethod)(void *);
typedef void (*VoidMethod)(void *);
typedef void (*MoneyMethod)(void *,int,int);
typedef void (*SpawnMethod)(void *,int,int,int);

static void *farm(void) {
    GetObject director = (GetObject)sym("_ZN7cocos2d8Director11getInstanceEv");
    ObjectMethod running = (ObjectMethod)sym("_ZN7cocos2d8Director15getRunningSceneEv");
    ObjectMethod children = (ObjectMethod)sym("_ZN7cocos2d4Node11getChildrenEv");
    CountMethod size = (CountMethod)sym("_ZNK7cocos2d6VectorIPNS_4NodeEE4sizeEv");
    void *(*at)(void *,int) = sym("_ZNK7cocos2d6VectorIPNS_4NodeEE2atEi");
    byte *vtable = sym("_ZTV9FarmScene");
    if (!director || !running || !children || !size || !at || !vtable) return 0;
    void *d=director(); if (!d) return 0;
    void *scene=running(d); if (!scene) return 0;
    void *list=children(scene); if (!list) return 0;
    int n=size(list); if(n<0 || n>1000) return 0;
    for(int i=0;i<n;i++) {
        void *node=at(list,i);
        if(node && *(void **)node == vtable+8) return node;
    }
    return 0;
}

__attribute__((visibility("default")))
int Java_org_cocos2dx_cpp_DevMenu_nativeApply(void *env,void *clazz,int command,int a,int b,int c,int d) {
    (void)env; (void)clazz;
    if(!game) game=dlopen("libMyGame.so",2);
    if(!game) return -1;
    byte *layer=farm(); if(!layer) return -2;
    void **global=sym("g_GData");
    byte *data=global ? *global : 0; if(!data) return -2;
    void *ui=*(void **)(layer+0x238);
    if(command==1) {
        if(a<0 || a>2 || b<1 || b>1000000000) return -4;
        const char *functions[]={"_ZN10GDataClass7getGoldEib","_ZN10GDataClass7getCashEib","_ZN10GDataClass7getRubyEib"};
        const char *refresh[]={"_ZN11FarmUiClass7setGoldEv","_ZN11FarmUiClass7setCashEv","_ZN11FarmUiClass7setRubyEv"};
        MoneyMethod add=(MoneyMethod)sym(functions[a]);
        VoidMethod update=(VoidMethod)sym(refresh[a]);
        if(!add || !update || !ui) return -1;
        int current=*(int *)(data+0x28+a*4);
        if(current<0 || current>2000000000) return -4;
        int room=2000000000-current;
        int delta=b<room ? b : room;
        if(delta) add(data,delta,1);
        *(int *)((byte *)ui+0x14c+a*4)=*(int *)(data+0x28+a*4);
        update(ui); return 0;
    }
    if(command==2) {
        /* The game has 24 tiers and 3 forms: displayed levels 1..72. */
        if(a<0 || a>23 || b<0 || b>2 || c< -1 || c>3 || d<1 || d>10) return -4;
        byte *monster=*(void **)(layer+0x234); if(!monster) return -2;
        CountMethod count=(CountMethod)sym("_ZN12MonsterClass15getMonsterCountEv");
        CountMethod eggs=(CountMethod)sym("_ZN12MonsterClass16getHatchEggCountEv");
        SpawnMethod spawn=(SpawnMethod)sym("_ZN12MonsterClass11makeMonsterEiii");
        VoidMethod save=(VoidMethod)sym("_ZN12MonsterClass11saveMonsterEv");
        if(!count || !eggs || !spawn || !save) return -1;
        int used=count(monster)+eggs(monster);
        if(used<0 || used>=120) return -3;
        int n=d < 120-used ? d : 120-used;
        for(int i=0;i<n;i++) spawn(monster,a,b,c);
        save(monster); return n;
    }
    return -4;
}
