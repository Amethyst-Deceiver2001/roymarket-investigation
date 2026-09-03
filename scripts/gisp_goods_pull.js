/*
 * scripts/gisp_goods_pull.js
 *
 * Full-roster sweep of gisp.gov.ru's public product catalog
 * (/mapm/api/product-list), one exact company_ogrn search per registry
 * entity with a known ОГРН (150 as of 2026-09-03).
 *
 * WHY A BROWSER SNIPPET, NOT A PYTHON SCRIPT: this endpoint sits behind
 * the same WAF/bot-protection challenge as the ПП719 registry
 * (gisp.gov.ru/pp719v2) documented elsewhere in this project — a plain
 * curl/requests POST gets an immediate 403 "Forbidden" from the WAF layer,
 * confirmed 2026-09-03. It only works from inside a real browser tab that
 * has already loaded gisp.gov.ru normally (the challenge is solved
 * automatically by the browser and cookied). So unlike zakupki_batch_pull.py
 * or egrul_batch_pull.py, this is NOT a `python3 scripts/...` command —
 * it's a snippet you paste into that browser tab's own DevTools console.
 *
 * This is the same "real work at scale against a live third-party
 * service" case the crawling-jobs policy in CLAUDE.md exists for (150
 * automated calls) — tested inline on a smaller sample first (11, then 40
 * entities, manually via chrome-devtools) before this full-roster version
 * was written. Per that policy it's handed to you to run yourself, not
 * executed by the assistant in the background.
 *
 * HOW TO RUN:
 *   1. Open https://gisp.gov.ru/goods/ in a normal browser tab and let it
 *      fully load (this clears the WAF challenge for the session).
 *   2. Open DevTools (F12) -> Console tab, on that same gisp.gov.ru tab.
 *   3. Paste this entire file's contents and press Enter.
 *   4. It runs ~150 sequential POSTs with a small delay between each
 *      (courtesy pacing, not required by the API) and prints progress to
 *      the console. Takes a few minutes.
 *   5. When done it logs a summary AND triggers a browser download of
 *      gisp_goods_pull_results.json (only entities with 1+ product hits;
 *      zero-hit entities are logged to console only, not saved, to keep
 *      the output file small).
 *   6. Save that downloaded file into data/sources/ as
 *      GISP_<YYYYMMDD>_goods-catalog-full-roster-sweep.json (fill in
 *      today's date), then hand it back for archiving through the normal
 *      inventory_sources.py -> scan_sources.py -> extract_registry.py ->
 *      check_registry.py pipeline — do NOT paste raw findings straight
 *      into corrections.json without that pipeline run first (this
 *      project's no-guessing/no-placeholder rule: every product claim
 *      needs a real source_id, which only exists after the file is
 *      archived and picked up by inventory_sources.py).
 */

(async () => {
  const targets = [{"slug": "ooo-mptm", "ogrn": "1257700021468"}, {"slug": "ano-tsbst-centre-for-unmanned-systems-technologies", "ogrn": "1247700190430"}, {"slug": "fond-nasha-pravda", "ogrn": "1237700218612"}, {"slug": "fond-gradislava-historic-cultural-heritage-preservation", "ogrn": "1117799007050"}, {"slug": "fond-dar-fond-regionalnykh-nekommercheskikh-proektov", "ogrn": "1067799028923"}, {"slug": "ooo-levit", "ogrn": "1066330007798"}, {"slug": "ooo-orion", "ogrn": "1077758220451"}, {"slug": "ooo-zavolzhskoe", "ogrn": "1133705000208"}, {"slug": "ooo-garant-klub", "ogrn": "5087746197622"}, {"slug": "ooo-finkonsaltingk-fkk", "ogrn": "1117746033052"}, {"slug": "fond-podderzhki-zimnikh-olimpiyskikh-vidov-sporta", "ogrn": "1117799016851"}, {"slug": "fond-podderzhki-natsionalnykh-morskikh-programm", "ogrn": "1167700057447"}, {"slug": "ao-seym-agro", "ogrn": "1114611000283"}, {"slug": "ooo-investments", "ogrn": "1237700523895"}, {"slug": "ao-borey-absorbed-no-longer-exists", "ogrn": "1247700237663"}, {"slug": "ao-spetstekh-investitsii-ao-spetstekh-pervyy", "ogrn": "1257700523079"}, {"slug": "ooo-sistemnyy-integrator", "ogrn": "1254600002920"}, {"slug": "pao-bank-psb", "ogrn": "1027739019142"}, {"slug": "ooo-aerotekhalyans", "ogrn": "1237700640660"}, {"slug": "ooo-zit-tsi-otraslevoy-tsentr-importozameshcheniya", "ogrn": "1227700802878"}, {"slug": "ao-uk-azimut-formerly-aeronavigatsionnye-i-informatsionnye-s", "ogrn": "1167746513967"}, {"slug": "ao-pk-azimut", "ogrn": "1057746261605"}, {"slug": "ooo-oupen-lodzhistiks", "ogrn": "1237700483976"}, {"slug": "npts-ushkuynik", "ogrn": "1245300001650"}, {"slug": "ovod", "ogrn": "1227100012369"}, {"slug": "ao-stratim", "ogrn": "1237700447324"}, {"slug": "ao-npp-bat", "ogrn": "1237700769701"}, {"slug": "ooo-kopterlab", "ogrn": "1247700198734"}, {"slug": "ao-tekhnodron", "ogrn": "1247700354175"}, {"slug": "ooo-atlant-aero", "ogrn": "1236100025633"}, {"slug": "ooo-gaskar", "ogrn": "1237700273744"}, {"slug": "ooo-skb-piranya", "ogrn": "1237300010430"}, {"slug": "ooo-aero-khit", "ogrn": "1232700009398"}, {"slug": "ooo-arkhangel", "ogrn": "1257700345407"}, {"slug": "ao-kotlin-novator", "ogrn": "1027806064571"}, {"slug": "ooo-kleverkopter", "ogrn": "1185275047176"}, {"slug": "ao-ploshchad", "ogrn": "1237700463032"}, {"slug": "ooo-npo-rustekhdron", "ogrn": "1235000022179"}, {"slug": "ooo-arkodim", "ogrn": "1101690020959"}, {"slug": "ooo-eyartek", "ogrn": "1227300004282"}, {"slug": "ooo-vizionero", "ogrn": "1195958038902"}, {"slug": "ooo-metaskan", "ogrn": "1201600057097"}, {"slug": "ooo-mentastep", "ogrn": "1247700255208"}, {"slug": "ooo-pekhtra", "ogrn": "1245200032406"}, {"slug": "yarl", "ogrn": "1237700170311"}, {"slug": "ooo-trimiks-bulat-3mx", "ogrn": "1237800084235"}, {"slug": "ooo-boevye-tekhnologii", "ogrn": "1235200037610"}, {"slug": "ooo-smart-teknolodzhis", "ogrn": "1127746712752"}, {"slug": "ooo-kravt", "ogrn": "1197847166560"}, {"slug": "ooo-opkb-eksplomet", "ogrn": "1211200001650"}, {"slug": "npo-kilobatt", "ogrn": "315582600002725"}, {"slug": "npp-elvo-kolskaya-verf", "ogrn": "1217800070509"}, {"slug": "ooo-superkhrono", "ogrn": "1163525102619"}, {"slug": "ooo-goudron", "ogrn": "1237700265846"}, {"slug": "va-technologies", "ogrn": "1252300058515"}, {"slug": "ooo-intek-bespilotnye-sistemy", "ogrn": "1247000000488"}, {"slug": "ooo-titan-severo-zapad", "ogrn": "1077847345179"}, {"slug": "ooo-sibirskaya-navigatsionnaya-kompaniya", "ogrn": "1184205024849"}, {"slug": "ao-prominvest", "ogrn": "1237700148180"}, {"slug": "ao-tekhnodinamika", "ogrn": "1037719005873"}, {"slug": "ao-aeromaks", "ogrn": "1227700471020"}, {"slug": "ooo-aeromaks", "ogrn": "1177746007900"}, {"slug": "ooo-gk-aeromaks", "ogrn": "1147748024269"}, {"slug": "ao-tsentr-telko", "ogrn": "1027739038590"}, {"slug": "ooo-dsg", "ogrn": "1207700030493"}, {"slug": "ooo-spetsialnye-poleznye-tekhnologii", "ogrn": "1247700253668"}, {"slug": "ooo-dron-reysing", "ogrn": "1187746574696"}, {"slug": "ooo-gaskar-integratsiya", "ogrn": "5147746074196"}, {"slug": "ooo-gaskar-tekhnologii", "ogrn": "1207700344037"}, {"slug": "ooo-vostochnye-vorota-zabaykalsk-manchzhuriya", "ogrn": "5167746405481"}, {"slug": "ooo-konstruktorskoe-byuro-sinergiya", "ogrn": "1237800134835"}, {"slug": "ooo-tsyus", "ogrn": "1181215007192"}, {"slug": "ooo-vozdushnyy-traktat", "ogrn": "1237100015767"}, {"slug": "ano-platforma-nti", "ogrn": "1197700000376"}, {"slug": "ooo-ushkuynik-sp", "ogrn": "1245300003827"}, {"slug": "ao-pmts-avangard", "ogrn": "1047855051892"}, {"slug": "ooo-zetaks", "ogrn": "1225300003983"}, {"slug": "npp-radar-mms", "ogrn": "1027807560186"}, {"slug": "ao-nii-vektor", "ogrn": "1117847020400"}, {"slug": "npts-elvis", "ogrn": "1127746073510"}, {"slug": "ao-ekolibri", "ogrn": "1217700279103"}, {"slug": "ao-mikts", "ogrn": "1227700322410"}, {"slug": "ooo-ekolibri-bt", "ogrn": "1237700545191"}, {"slug": "ooo-promsintez", "ogrn": "1073435002013"}, {"slug": "ao-uk-smart", "ogrn": "1237700557050"}, {"slug": "ooo-kingpro", "ogrn": "1247700607450"}, {"slug": "ooo-kravt-udmurtiya", "ogrn": "1241800012222"}, {"slug": "ooo-spdbbk", "ogrn": "1157847359273"}, {"slug": "ooo-stratim", "ogrn": "1245200009075"}, {"slug": "ao-aurin", "ogrn": "1237700898786"}, {"slug": "ooo-ayaks-tekhnologii", "ogrn": "1187847150699"}, {"slug": "ao-korporatsiya-sinergiya", "ogrn": "1237700250182"}, {"slug": "ooo-rokot-tekh", "ogrn": "1247600010954"}, {"slug": "ao-fabrika-im-sovetskoy-armii", "ogrn": "1027739157401"}, {"slug": "ooo-nova", "ogrn": "1086330002549"}, {"slug": "ooo-ges-2", "ogrn": "1147746575767"}, {"slug": "ooo-vingrad", "ogrn": "1177746217879"}, {"slug": "ooo-stroystandart", "ogrn": "1077762402992"}, {"slug": "ooo-orzhitskie-artezianskie-vody", "ogrn": "1197746619950"}, {"slug": "ao-khk-gumich", "ogrn": "1237700537788"}, {"slug": "gk-rostekh", "ogrn": "1077799030847"}, {"slug": "ao-glavtekhkonstruktsiya", "ogrn": "1174632000190"}, {"slug": "zao-kurskpromteplitsa", "ogrn": "1117746195214"}, {"slug": "ooo-npo-nebo", "ogrn": "1254800002786"}, {"slug": "ao-nii-stt", "ogrn": "1026701461160"}, {"slug": "ooo-tsentr-dinarus", "ogrn": "1245000015952"}, {"slug": "ooo-orient-sistems", "ogrn": "5147746083491"}, {"slug": "ooo-4gnss", "ogrn": "5157746074272"}, {"slug": "ooo-aeroplatformy", "ogrn": "1215000018650"}, {"slug": "ooo-krams", "ogrn": "1237700290112"}, {"slug": "ooo-prommash", "ogrn": "1244200002970"}, {"slug": "ooo-dronomir", "ogrn": "1264200005530"}, {"slug": "ooo-instekh", "ogrn": "1207800035079"}, {"slug": "ooo-asel-labs", "ogrn": "1257700126958"}, {"slug": "ooo-gagaring", "ogrn": "1232300051235"}, {"slug": "ooo-praym", "ogrn": "1097746825945"}, {"slug": "ooo-tstp-tsifrovaya-transportnaya-platforma", "ogrn": "1247700498660"}, {"slug": "ao-spetstekh-perviy", "ogrn": "1267700128376"}, {"slug": "kolskaya-verf", "ogrn": "1245100006799"}, {"slug": "ooo-ti-es-dzhi-grupp", "ogrn": "1233200001066"}, {"slug": "ooo-npts-basirtk", "ogrn": "1243300000789"}, {"slug": "ano-tsasd-demyansk", "ogrn": "1235300001947"}, {"slug": "ano-tsentr-razvitiya-transportnykh-tekhnologiy", "ogrn": "1217700636306"}, {"slug": "ooo-gk-logos", "ogrn": "1253400004527"}, {"slug": "bf-ktspn-barnaul", "ogrn": "1152225001114"}, {"slug": "assotsiatsiya-vzaimopomoshch", "ogrn": "1164700050734"}, {"slug": "ooo-rt-razvitie-biznesa", "ogrn": "1147746392200"}, {"slug": "ooo-tsugam", "ogrn": "1227700378553"}, {"slug": "ooo-akr-begak", "ogrn": "1202600009919"}, {"slug": "ano-arrs-krasnodar", "ogrn": "1242300011469"}, {"slug": "ao-ross", "ogrn": "1027700135957"}, {"slug": "ooo-npo-kilovatt", "ogrn": "1244800001820"}, {"slug": "ooo-npo-kilovatt-shestopalov", "ogrn": "1244800005240"}, {"slug": "ooo-pokrov", "ogrn": "1245000068774"}, {"slug": "ooo-tsentr-bespilotnykh-sistem-tula", "ogrn": "1237100001467"}, {"slug": "ooo-rtd-zashchita", "ogrn": "1225000111313"}, {"slug": "ooo-btr-bespilotnye-tekhnologicheskie-resheniya", "ogrn": "1247800059980"}, {"slug": "ooo-spetsmat-spetsialnye-materialy", "ogrn": "1247800116464"}, {"slug": "ooo-npk-tspt-tsentr-perspektivnykh-tekhnologiy", "ogrn": "1265300000470"}, {"slug": "ano-ntsns-nevskiy-tsentr-nauchnogo-sotrudnichestva", "ogrn": "1127800002175"}, {"slug": "ooo-geron", "ogrn": "1217800073545"}, {"slug": "ooo-skay-avia-grupp", "ogrn": "1147847241464"}, {"slug": "ooo-npk-geron", "ogrn": "1187847365750"}, {"slug": "ooo-akatsiya-avia", "ogrn": "1027801572820"}, {"slug": "ooo-aero-khit-servis", "ogrn": "1237700611455"}, {"slug": "ooo-aero-khit-m", "ogrn": "1267700066006"}, {"slug": "ooo-btr-donetsk", "ogrn": "1249300018582"}, {"slug": "ooo-intel-dron", "ogrn": "1247400026246"}, {"slug": "ooo-npo-eyler", "ogrn": "1257100008560"}, {"slug": "ano-dpo-obrazovatelny-tsentr-gagaring", "ogrn": "1252300026208"}];

  const results = {};
  let hitCount = 0;

  for (let i = 0; i < targets.length; i++) {
    const {slug, ogrn} = targets[i];
    if (!ogrn) continue;
    try {
      const r = await fetch('/mapm/api/product-list', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          page: 1,
          per_page: 100,
          filters: {status_code: 'product', company_ogrn: ogrn},
          type: '[Product] Query'
        })
      });
      const j = await r.json();
      const total = j && j.meta ? j.meta.total : 0;
      if (total > 0) {
        hitCount++;
        results[slug] = {
          ogrn,
          total,
          company: j.data[0].company,
          products: j.data.map(p => ({
            id: p.id,
            name: p.name,
            okpd2: p.okpd2 ? p.okpd2.name : null,
            hasActiveCertificate719: p.hasActiveCertificate719,
            hasActiveCertificateOther: p.hasActiveCertificateOther,
            ektruDp: p.ektruDp
          }))
        };
        console.log(`[${i + 1}/${targets.length}] HIT  ${slug} (${ogrn}) -> ${total} product(s)`);
      } else {
        console.log(`[${i + 1}/${targets.length}] ---  ${slug} (${ogrn})`);
      }
    } catch (e) {
      console.error(`[${i + 1}/${targets.length}] ERROR ${slug} (${ogrn}):`, e);
    }
    // Courtesy pacing - not required by the API, just polite.
    await new Promise(res => setTimeout(res, 300));
  }

  console.log(`\nDone. ${hitCount}/${targets.length} entities have GISP catalog products.`);
  console.log(results);

  const blob = new Blob([JSON.stringify(results, null, 2)], {type: 'application/json'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'gisp_goods_pull_results.json';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
})();
