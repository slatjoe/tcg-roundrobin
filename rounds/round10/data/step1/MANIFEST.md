# Step 1 pilot — data MANIFEST (staged 2026-10-30)

Provenance: fetched read-only from the sim box (golf-gamer) on 2026-10-30 via a single tar stream over the established ssh-box.sh Tailscale-tunnel route. Box source root: `/home/joe/tcg/r10pilot_out/`. Layout mapping: box `pregate/attempt2/` is staged here as `pregate_attempt2/`; all other paths mirror the box. Box file mtimes preserved by the fetch.

Not fetched: the unix socket files on the box (`games/srv_s1.sock`, `games/srv_s2.sock`, `l3/prod_s1.sock`, `l3/prod_s2.sock`, `pregate_attempt2/srv_s1.sock`, `pregate_attempt2/srv_s2.sock`) — runtime artifacts, zero bytes of content, not archivable. Everything else under the source paths is present.

Cross-verification: every sha256 recorded in the run's own `pilot_manifest.json` was checked against the fetched bytes and MATCHES (games x4, jobs_all + all shard/part files, labels_all + all 8 shard parts, games_report.json, pilot_read.json; the manifest's flat `search_stats.jsonl` entry is `games/games_s2b_log/search_stats.jsonl` and its `teacher_snap_index.jsonl` entry is `games/games_s2b_log/snaps/teacher_snap_index.jsonl` — both match).

## Files (sha256, bytes, path)

```
c676b7b16e98f7174b8a5667b66fd07e61dbe06ba940002bdf8145cffb6b4a07         316  pilot.launch.log
a6c739bc11a269a13a19ada8cc8a8046fbf2c3621d5723ad5308c3165500f250        2000  pilot.launch2.log
031169758035565aca713b3dbfb07d915972f55b832ea567995be1cefa7a4018        8512  pilot_manifest.json
9ca657a8c411f3a7ee9f439cac5c95f60c0e66af28c28fa027beaba6563a827a        3032  pilot_read.json
70e87d59781c5123766a42d09a50539003e337803db8af6a6c93f6c3771043a4        1228  pilot_read.txt
e1b413b8e89bc2f9b641700a51dfe4447bfc2519d72054da3d42ae7a13e268e2         395  pregate_attempt2.launch.log
d3be0af034b4761b7946f59d8a3925f92935ee9f5fe7595e0fb8a76505178e14         301  pregate_runner.log
9bf8df5b8c67fddc84b50242ed6a851cf691d5f47543608e069f8bcd3c2761ad        2094  games/deployed_code_hashes.txt
a85c76c0eb8fba586bdf8bac27abdcf451017e61cdb107c08776ab0d1b6320e8         120  games/g8_pilot_after.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855           0  games/g8_pilot_attached_kept.txt
c8b9fd5de5e59dc3eda370bbe4b209eca557129ea2f9fcac10e1746b5906cd54         200  games/g8_pilot_before.txt
d278e9f578073496ecfeee69f36fd7175de06b7ef263085f8eb302c2cb919ee8           8  games/g8_pilot_stale_ids.txt
5b7f92a4108130fa6267e5ad7869709516b46231dfebeb8eceb08b77f14cdd0e        1156  games/games_report.json
1c35328a2e0e80482119b8fc5eab29b9731fe467beab994c5b23def213bc7219         433  games/games_report.txt
bbadf501d74a3189dd03540e405aedf0f48d06fcad74aa3ea09f70cc001fcb0c       14556  games/games_s1a.jsonl
e0e88b4d8ab833bde99a337cfb128512dd37ef725660febf3fe088e520a0b3c9         771  games/games_s1a.jsonl.manifest.json
4ce9d160806f0b94d00388466b4103015f7eb79b76da449fbc01bb179fce7e92        1126  games/games_s1a.stdout
3b1e4bb5ff9b99aacd5747043b5f209bc6011b60b66b9a76b58602ab7db7d60b         250  games/games_s1a_ids.txt
f944e539bc367fbc07d9519ce0619c672e117522267bf8f1927a24b8209464f9       14552  games/games_s1b.jsonl
604863ace9e9e8a4eeba4fe8fc8591c1166cc0b4b4f0203b7549660b918b944c         771  games/games_s1b.jsonl.manifest.json
82fc68d4eda52fe31168b2956f40844f06603d74dd02d2484ff695b62bcf2365        1128  games/games_s1b.stdout
87e2c9bea9155d9596d5d87214dade644bf20b324bf4cd325994ab8e4ec0858b         250  games/games_s1b_ids.txt
991ab1adb6395051fd72c1b94ae1f8058d9336a4b8c042c00431b152b2008560       14548  games/games_s2a.jsonl
cc64fe0f5a4bf40a29d059f9f293216b8c6492cb999fa0cdc8be9337226c4a44         771  games/games_s2a.jsonl.manifest.json
d3b173106c0e2562393c8f6e9af2c645f52f61c326908cad78a5fd62dafde4eb        1128  games/games_s2a.stdout
7c37d199d2898c28138895ec7666d3079dfaa1b499c44288480e8fbec8cc9eed         250  games/games_s2a_ids.txt
9d7ff36454c045066e142407eaf978662e0dba5f3afe2a7b9d2da5a4716ff2c0       14551  games/games_s2b.jsonl
bf4dd4331ec50cc1302ff87f4b0111c17686b506ab1bed4723977f8652ad6835         771  games/games_s2b.jsonl.manifest.json
8edcc5c54feb240ad452876a0e5f25a56d46d3d1b85f0e2a3b449e0c347145cc        1125  games/games_s2b.stdout
cbc7a07c5d0de3033e305a78f95b9bd0d3e4976ed52210fba2fe02adba5c86d8         250  games/games_s2b_ids.txt
a85c76c0eb8fba586bdf8bac27abdcf451017e61cdb107c08776ab0d1b6320e8         120  games/ipcs_gm_s1a.txt
a85c76c0eb8fba586bdf8bac27abdcf451017e61cdb107c08776ab0d1b6320e8         120  games/ipcs_gm_s1b.txt
a85c76c0eb8fba586bdf8bac27abdcf451017e61cdb107c08776ab0d1b6320e8         120  games/ipcs_gm_s2a.txt
a85c76c0eb8fba586bdf8bac27abdcf451017e61cdb107c08776ab0d1b6320e8         120  games/ipcs_gm_s2b.txt
458c2db15799c84ffb1af29f7ac2f24963cf368de862401b1adb0378e12c17b0         200  games/ipcs_l3_0.txt
458c2db15799c84ffb1af29f7ac2f24963cf368de862401b1adb0378e12c17b0         200  games/ipcs_l3_1.txt
458c2db15799c84ffb1af29f7ac2f24963cf368de862401b1adb0378e12c17b0         200  games/ipcs_l3_2.txt
458c2db15799c84ffb1af29f7ac2f24963cf368de862401b1adb0378e12c17b0         200  games/ipcs_l3_3.txt
6d4ef9e2db2122c915fcf0c90a9d80bc013289262ac3d88e29f39e1ab106a7c6         329  games/registry_merge.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855           0  games/shm_start_gm_s1a.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855           0  games/shm_start_gm_s1b.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855           0  games/shm_start_gm_s2a.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855           0  games/shm_start_gm_s2b.txt
a0572bb3088fc7b5ad5b7d1c0b612e7c7d44d7f347f06aec787da49e390be0fc          10  games/shm_start_l3_0.txt
a0572bb3088fc7b5ad5b7d1c0b612e7c7d44d7f347f06aec787da49e390be0fc          10  games/shm_start_l3_1.txt
a0572bb3088fc7b5ad5b7d1c0b612e7c7d44d7f347f06aec787da49e390be0fc          10  games/shm_start_l3_2.txt
a0572bb3088fc7b5ad5b7d1c0b612e7c7d44d7f347f06aec787da49e390be0fc          10  games/shm_start_l3_3.txt
adbcdd12a0ecfcd812fdec81ae52ddcd31f8ffe7f79d870b48271e46663a1b13      102629  games/shm_sweep_gm_s1a.log
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855           0  games/shm_sweep_gm_s1a.stop
13e1ef2655d73fd081b19f3f0c3df7236a8e05de59a3b0336ae36d4d1c61a50f       85111  games/shm_sweep_gm_s1b.log
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855           0  games/shm_sweep_gm_s1b.stop
c352083b1b8365838ea00948657d8d15a3fe2838b72914b49269da2e017391f3       80814  games/shm_sweep_gm_s2a.log
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855           0  games/shm_sweep_gm_s2a.stop
3822c2b6fdb8460bae5e392c67f8eb9eba220e4d592fef40bddeadadbe5c79c0       81005  games/shm_sweep_gm_s2b.log
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855           0  games/shm_sweep_gm_s2b.stop
ed2c0debf667366523faf865f571feed4e5dabba0694855b8ae4289fdb9bd05d       30064  games/shm_sweep_l3_0.log
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855           0  games/shm_sweep_l3_0.stop
76943db5175df17b78ff94adc998e4d3b09d6ea66d741f1f252575732c3365a1       12287  games/shm_sweep_l3_1.log
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855           0  games/shm_sweep_l3_1.stop
fbef545b0d06dcc36486d36d7b04af840a272b519ca1003bf0176746397d8692       12288  games/shm_sweep_l3_2.log
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855           0  games/shm_sweep_l3_2.stop
3c099df19b51d1e839b8f6410b430aae689fc86421618ddc264836f964336f27       12290  games/shm_sweep_l3_3.log
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855           0  games/shm_sweep_l3_3.stop
3bbeb37b1cdd0335d8eeaa8683a3b1598b2a2a8b498bc8567a808b14a2f25589      177839  games/srv_s1.log
48af4ce56f6e568e12b9021d86f23d9c3cd5c04c6480c533ede15f7c875d00f5      179245  games/srv_s2.log
26d6cf3e5e8e84079c59d5fbb4e9c8bc60f508849dc90a43ea9e2cbe79c28952      891186  l3/jobs_all.jsonl
2df1bf686ad76518d33cd411865b3e8f5c0c5f8ea0d865d44c4aef431fc1973b         391  l3/jobs_report.json
9a856781d3f518bbd1fc52fc2caca5058e4b082103ed1a75a6df1184d6e3613e      221242  l3/jobs_shard0.jsonl
2d5d66f34d3dcc71e1d30969685cfd2afd980cca7517b451c4fb89543987cbf2      124321  l3/jobs_shard0_p1.jsonl
a332407d68b448ff58672627ad142ffe5e0d517ef2c49974294e90d91821d140       96921  l3/jobs_shard0_p2.jsonl
ace1114129637555371807482dd6d93d7e92a82164c6ee1084c9007fcfd5bf28      146882  l3/jobs_shard1.jsonl
7bc0be6ae1bd0678026b2d026f860f1c8ab5a6d131e5cf86529a23550f64f249       86089  l3/jobs_shard1_p1.jsonl
99752895ff4f9d0e493e6c90e067f344786d0cfa9f16682533d300cf858c0a8e       60793  l3/jobs_shard1_p2.jsonl
24cb2e041bfdb61f902ff7e103c5eaaec71d377dbfc528b40ec3981443384948      263693  l3/jobs_shard2.jsonl
1203d447143923a3e3a9b85a8a5643caecb0013dc0062169605182969099fec4      170424  l3/jobs_shard2_p1.jsonl
45ba34b224065f25c8210a64229a98800745fb462f355f6b442101ecd86937fe       93269  l3/jobs_shard2_p2.jsonl
368df61278bde489a90ceae21c89ebdbbac2554adc7477ec77b2a5c8bc52906a      259369  l3/jobs_shard3.jsonl
89cf2fc372e248512db805aab056458191ff2085b3332e97a86885c065a8b994      133897  l3/jobs_shard3_p1.jsonl
45efed0a7dd8bbd5ac1ea276a176920f5b3867bd69d4e5219096c6eab71bc500      125472  l3/jobs_shard3_p2.jsonl
6756447adabb9b316d6e270acafddf61148871513679b64378396414cdbb4e0c        5058  l3/label_shard0_p1.err
181f6fe1544f1c0ed5fe4e6b8b624b8c68d1bc554916677730ee5865c45a9bc4        3984  l3/label_shard0_p2.err
dafde06f20b74f868a76cc91ea236d32f411e65f12875e6fce9f65a6b596c42d        3325  l3/label_shard1_p1.err
ea1397b50cbb34ca562af58361943a698522b74157eb7f10d56aa72b294722fa        2495  l3/label_shard1_p2.err
6158505204e842eab7abedfebdd6ae0ec9f618c362042f140ff3651249e3394b        6327  l3/label_shard2_p1.err
6801b870e90dfed13b7aa32f8d22c75107578d69cd44425b93f4e31fbb0519c3        3681  l3/label_shard2_p2.err
7a3cf5d68609d1d7a0732c45a2d7bc8f906c91d94c08c70e86e80cb479f7bce1        4651  l3/label_shard3_p1.err
68cfccd7fa7d4c79850618a19c8486270d33ded0ee1f0fd59e1a413de8068e5f        4925  l3/label_shard3_p2.err
94d110c1881a33559dbc5b38da19a0d4ea9d8426616053d65f97a7181297df3b       37129  l3/label_stats_shard0_p1.jsonl
fb1ab874dfd291a6826e3b8c17d142ea271f4d7277dabdabb74733279c93dec9       28884  l3/label_stats_shard0_p2.jsonl
f4a71c8ef8cc9e295f9b53c15d12f4991c9af4f4616a7d12387c34c802b6dd21       23796  l3/label_stats_shard1_p1.jsonl
6c67f85ca228dcb5d26e4707b43697b7104ad58982b1918f25b5e2c13d56c61a       17457  l3/label_stats_shard1_p2.jsonl
b693de16ea123e3c0fc024db2eb960dd22cd6ff1b056b553f0dd2984824ff616       46971  l3/label_stats_shard2_p1.jsonl
6725e7bb1e51921cf11916af37cd50cc5a8d4351073cc935e130d93de87cd59b       26637  l3/label_stats_shard2_p2.jsonl
f088e9f71929d7e6fb96e3bbd1eff2802f623394a88d65f894b02813971d3774       33965  l3/label_stats_shard3_p1.jsonl
2cc97d217a3e7e1f7bb78dc3647cc3fc36b3109d1a05af5950094c36a71c91d8       36169  l3/label_stats_shard3_p2.jsonl
9180824843895191ef99492ad88d9eaa44a0e46e0431e24aaf23fb39c87a2a75   241460621  l3/labels_all.jsonl
deefc6d3fd79b2c9bebdd7a87c7c236ca34b62e4122e967ce5cbde04986762b5    35359094  l3/labels_shard0_p1.jsonl
5c466b5ca4274ba76d0b9600c11bc8a6d19f8fbe7d11f9375ac5112a7c4f196e    26965525  l3/labels_shard0_p2.jsonl
f84b2fb1c48590747c5efbd1b718e1dc965f7f8f87fe9d86dbe7806ce5d95190    23763578  l3/labels_shard1_p1.jsonl
9ff1a7c5474a09dfb1f4a0a49ebc1efbf631745f28719735064684f0fa94ba76    16222123  l3/labels_shard1_p2.jsonl
9b27adaa2961ab0c906e3638f50dc2620cfa10dafe08a017434be2c21b68982a    45210734  l3/labels_shard2_p1.jsonl
e4f299c1af8942e7d6dc2004105d519fb46182169226966c7b96949619c23af9    25551111  l3/labels_shard2_p2.jsonl
26f9b39ecb49ba277c5bc9538933fdfb81cef30202c5594eeeb08a30c43aaf89    33724758  l3/labels_shard3_p1.jsonl
e6a59ea0e047c5174ae9a3bbe2e98b24896661e26ebdd35438ea46752c011e23    34663698  l3/labels_shard3_p2.jsonl
ab203e3cc0d147c6a744f5310f9142b2dfb598cea886dc56aec46bdfc67ee1c6       19794  l3/prod_s1.log
23a37de40a48f4798d916318b12d197e072720317dacf11b1a6c8061a649fa10       12546  l3/prod_s2.log
dfe41e8c01c89b7847bb3e05fe27f08a04223bddf38d46c98f171ce15b83f774         934  pregate_attempt2/deployed_code_hashes.txt
a85c76c0eb8fba586bdf8bac27abdcf451017e61cdb107c08776ab0d1b6320e8         120  pregate_attempt2/g8_pregate_after.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855           0  pregate_attempt2/g8_pregate_attached_kept.txt
f70f799dc1dd1e599abf539de42626653f7e410a0c73cfc6c1766b6768b0c121         200  pregate_attempt2/g8_pregate_before.txt
b972d6a7926a7115b514dae3b5989bb581d64f2afb4bc879766d0e76c94fb674          11  pregate_attempt2/g8_pregate_stale_ids.txt
a85c76c0eb8fba586bdf8bac27abdcf451017e61cdb107c08776ab0d1b6320e8         120  pregate_attempt2/ipcs_pg_ghost14_s1.txt
a85c76c0eb8fba586bdf8bac27abdcf451017e61cdb107c08776ab0d1b6320e8         120  pregate_attempt2/ipcs_pg_ghost14_s2.txt
a85c76c0eb8fba586bdf8bac27abdcf451017e61cdb107c08776ab0d1b6320e8         120  pregate_attempt2/ipcs_pg_ghostthr_s1.txt
a85c76c0eb8fba586bdf8bac27abdcf451017e61cdb107c08776ab0d1b6320e8         120  pregate_attempt2/ipcs_pg_ghostthr_s2.txt
b5b0390a457a59cc09c740cc9abf252f443c2d4be9f00e16ca473d4db99186a1         700  pregate_attempt2/pg_all_ids.txt
17fbf552d996abcbbbe5af0ef727d0085f439ad658973a70d71770351c5ff220        5907  pregate_attempt2/pg_ghost14_s1.jsonl
e0dd9f09a354031d775dfcb6eca67682ac988cc8d91655ffaafe3ce1fb1aa29a         844  pregate_attempt2/pg_ghost14_s1.jsonl.manifest.json
dea999df04573b6c6272bb206a49823bf80fa1244bba731378fc44bf00a7c252         511  pregate_attempt2/pg_ghost14_s1.stdout
ba5ec8f385521d0470a1533a82a9f43aa4be7909d6d0e1fed17f21b3b0483e10         100  pregate_attempt2/pg_ghost14_s1_ids.txt
38090f0e6d57c50945576677173aa66152733bb87fb47891b26158b3ca9429d5        5901  pregate_attempt2/pg_ghost14_s2.jsonl
fa7f156906e24524a5c79e6443b155e84db6e5672a10ddabc0b1b01a94003a4a         844  pregate_attempt2/pg_ghost14_s2.jsonl.manifest.json
d79d78fec8feaed6675b60710242f36106922c8f60241b05868c406420a356c4         511  pregate_attempt2/pg_ghost14_s2.stdout
4cf1d2f90b601dade5a775995c464bd799df3a53018d51b9d17e8648022e1ae4         100  pregate_attempt2/pg_ghost14_s2_ids.txt
ce2d8ba0edc0a988fd20245d448494da1c940e345be01b8f0aec3354175dd7f9        5913  pregate_attempt2/pg_ghostthr_s1.jsonl
987d5687cd98e3b6b3379b9ff28515d661382d7c42401b861445d26e202d4b57         845  pregate_attempt2/pg_ghostthr_s1.jsonl.manifest.json
14cd10742d2118b61c0fc56f01ac821d693edb0015d00a1cac4334db674b0185         517  pregate_attempt2/pg_ghostthr_s1.stdout
1a07924e64c4ffa4125b5875745d3e38ebe366a24c522716d6f72ec44fa26a15         100  pregate_attempt2/pg_ghostthr_s1_ids.txt
90a61852564451aa59ecc5ee1dc6ecd4973d9132c82589934b9129b8222be5e1        5908  pregate_attempt2/pg_ghostthr_s2.jsonl
6147d11004d9dbe6a30a1122662a2886d814dca10a4245488ef2d806b2a76816         845  pregate_attempt2/pg_ghostthr_s2.jsonl.manifest.json
436ec5c802fb24cbf22d97cc50ec325c2f6e4ec5b0d9389f1d98d2371fbdf31b         518  pregate_attempt2/pg_ghostthr_s2.stdout
0b51e0d2a66fd390717603f29de8b15d515db4193c2152fb0a7112578a91030f         100  pregate_attempt2/pg_ghostthr_s2_ids.txt
13d8e261d600652f0e1376317f5775df6e47f11d053311d9107e24083a77a371        5497  pregate_attempt2/pg_raw2_s1.jsonl
c0cbe3596bac66e0a8956a7e093c40188e29c4be82bafbd56a29d0dbf0c65fe8         670  pregate_attempt2/pg_raw2_s1.jsonl.manifest.json
c894cbe2a9bf827dac62669d7c27df65c35cd73be0e61d53e473795cc097a795         469  pregate_attempt2/pg_raw2_s1.stdout
f3454be39b1738f9b69844d3da43e4f743fef393f432a54de97a06cfb3e76d86         100  pregate_attempt2/pg_raw2_s1_ids.txt
8a7d14dbb500f24e41d7315151aadf1c84f4bbac0b80ba8570d995b91bb7f203        5497  pregate_attempt2/pg_raw_s1.jsonl
c0cbe3596bac66e0a8956a7e093c40188e29c4be82bafbd56a29d0dbf0c65fe8         670  pregate_attempt2/pg_raw_s1.jsonl.manifest.json
243617c39cd64017ce7168d1dac48905dd1a8e04f13e9d338d408a04728abfbd         469  pregate_attempt2/pg_raw_s1.stdout
c61dd219f60748c46d32a328ea3e1b31fd181359a6404a4dfbb78d0d9950fe89         100  pregate_attempt2/pg_raw_s1_ids.txt
d9b8d0d2888d3371468ca3c829151a58913deaa366ffe7e2a25f5799674d71a6        5491  pregate_attempt2/pg_raw_s2.jsonl
4aa26cc4ed7b53514e988e3c81ca613c6a418da9f7eb166eb7ccfe94e00527b0         670  pregate_attempt2/pg_raw_s2.jsonl.manifest.json
de5abcc840e419f4166c37990cd2b36aa0fa8e6d8beb750197ba326169522c4c         469  pregate_attempt2/pg_raw_s2.stdout
2804551ab5575d8d7cb4c7384cecac761484fdcbc4010e7f3909bd23f15a2e21         100  pregate_attempt2/pg_raw_s2_ids.txt
a6e33f105857bc735fa7db308b8b0a7311c6e8c8e75cd126a5e0bfb7891091de        2380  pregate_attempt2/pregate_check.txt
685fefa337f7b8f13f0d5dabc8ef95184e4e469b18ff1d91877b774bb5bb832f        4476  pregate_attempt2/pregate_manifest.json
479b8b2ec42be44e8b37bf1357741df5533c67ff6bca3c4ee1a16a3e0f2a074e         336  pregate_attempt2/registry_merge.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855           0  pregate_attempt2/shm_start_pg_ghost14_s1.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855           0  pregate_attempt2/shm_start_pg_ghost14_s2.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855           0  pregate_attempt2/shm_start_pg_ghostthr_s1.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855           0  pregate_attempt2/shm_start_pg_ghostthr_s2.txt
2ec576e286a209d4db33d1ab54f3a407d2ca38ae8d3dcbe5357172a10dea7760       32883  pregate_attempt2/shm_sweep_pg_ghost14_s1.log
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855           0  pregate_attempt2/shm_sweep_pg_ghost14_s1.stop
714e2c36f6468ddd352d8c8cf5aa8728b9b0ba7fb04a88670dbd09849ac2a03b       21104  pregate_attempt2/shm_sweep_pg_ghost14_s2.log
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855           0  pregate_attempt2/shm_sweep_pg_ghost14_s2.stop
f1f48216620b9dcb9e6edf8f4fa82e6c8e3becc9af740f83feb503a1d2f8ca5f       19234  pregate_attempt2/shm_sweep_pg_ghostthr_s1.log
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855           0  pregate_attempt2/shm_sweep_pg_ghostthr_s1.stop
27bb303127676ab64d1ebc70e14b1dc012eca5fce3923a57ae4de9ffa599b033       19231  pregate_attempt2/shm_sweep_pg_ghostthr_s2.log
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855           0  pregate_attempt2/shm_sweep_pg_ghostthr_s2.stop
6da6c6c066aad87d618c693d2fcb164b135d4ce0568418e5e7475ec2e7d698b9       37542  pregate_attempt2/srv_s1.log
a242683b20b88793df9b2cf4cbeebcded82306f30052bf52af4db8636186c725       40166  pregate_attempt2/srv_s2.log
```

## Log/snapshot trees (aggregate entries)

Each `*_log/` directory holds per-game server logs, decision traces and snapshot directories (thousands of small files). Each is covered by one aggregate entry: file count, total bytes, and a tree digest = sha256 of the sorted lines `<sha256>  <path>` over every file in the tree.

```
7c64fd922b2c6a9b1f84224d854599899ce5094149e9a3342165231dd969ea25  files=3571 bytes=44957058  games/games_s1a_log/
e0942783a1a2a36d6b8dd33a332215be94c84eae28a36ddf0b7ca0b53fe6c5e7  files=3688 bytes=43149554  games/games_s1b_log/
c490537094ff4c03547a18b4025f428e2d8ff7fb0ffadba214770abb5f198054  files=2985 bytes=32037025  games/games_s2a_log/
b6c88a55351ad81eac4c7acef07c1c8623389d0ebc8af7670d43450ba5268bef  files=2587 bytes=30270656  games/games_s2b_log/
b47ec847aa2a63dcdaad1b8d240c380c4d564c14dcd2887411bb2502bbda29d5  files=11 bytes=2356962  pregate_attempt2/pg_ghost14_s1_log/
b50df741a68802b0fb053c87336cbe1ffb36ab7d6e76a11149d597400b90dbfc  files=11 bytes=2232392  pregate_attempt2/pg_ghost14_s2_log/
72838db50932f492fc778343592d13b44e7aa059d9f219fe79f502e283c0e8c7  files=11 bytes=2887091  pregate_attempt2/pg_ghostthr_s1_log/
245a881fb61637b62db3ebc1cd5fd052c9519b75c843d52b69c8ade83ba8edad  files=11 bytes=2765018  pregate_attempt2/pg_ghostthr_s2_log/
3f4203527c0ef3579acee04741a0f34f79af57bb2250a7babf62246d139e8bc7  files=10 bytes=1470143  pregate_attempt2/pg_raw2_s1_log/
cb591261491a993707f5ed2a45f87b1810232711c50808c6ffd4ec404eb7ac52  files=10 bytes=1470143  pregate_attempt2/pg_raw_s1_log/
05c69b2f51993d3a5c856d60dfd21dc41c78f44ef22edade0ec29a92c8fb79bb  files=10 bytes=1399061  pregate_attempt2/pg_raw_s2_log/
```

Totals: 13066 files, 651999365 bytes staged (plus this MANIFEST.md).
