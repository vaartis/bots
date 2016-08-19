extern crate regex;

use libtabun::{TClient,Comment,CommentType,HOST_URL};

use std::collections::HashMap;
use std::{fs,thread,time};
use std::io::{Read,Write};

use regex::Regex;

fn check(user: &mut TClient, comms: HashMap<i64,Comment>) {
    let pre_regex = Regex::new(r"<pre>[\s\S]*</pre>").unwrap();
    let quote_regex = Regex::new(r"<blockquote>[\s\S]*</blockquote>").unwrap();
    let name_regex = Regex::new(r"@(?P<name>[\w\\-]+)").unwrap();

    for comm in comms.values().by_ref() {
        let mut body = comm.body.clone();
        let was_answered = comms.iter().by_ref().any(|(_,ref x)| x.parent == comm.id && x.author == user.name);
        if body.contains("@er16 ignore") {
            if !was_answered {
                let mut content = String::new();
                {
                    let mut f = fs::File::open("ignore.lst").unwrap();
                    let _ = f.read_to_string(&mut content);
                }
                let ignore_lst = content.split("\n").collect::<Vec<_>>();
                match ignore_lst.iter().position(|&x| x == comm.author) {
                    Some(x) => {
                        let mut new_content = ignore_lst.clone();
                        let _ = new_content.remove(x);
                        let mut f = fs::File::create("ignore.lst").unwrap();
                        let _ = new_content.iter().map(|&x| writeln!(&mut f,"{}", x));
                        let _ = f.sync_data();
                        let _ = user.comment(comm.post_id, "Игнорирование выключено", comm.id, CommentType::Post);
                    }
                    None => {
                        let mut f = fs::OpenOptions::new()
                            .append(true).open("ignore.lst").unwrap();
                        let _ = f.write_all(format!("\n{}", comm.author).as_bytes());
                        let _ = f.sync_data();
                        let _ = user.comment(comm.post_id, "Игнорирование включено", comm.id, CommentType::Post);
                    }
                }
                continue
            }
        }

        if pre_regex.is_match(&body) {
            body = pre_regex.replace_all(&body, "");
        }
        if quote_regex.is_match(&body) {
            body = pre_regex.replace_all(&body, "");
        }
        if name_regex.is_match(&body) {
            if !was_answered {
                let mut names = name_regex.captures_iter(&body).map(|x| x.name("name").unwrap()).take(10).collect::<Vec<_>>();
                names.sort();
                names.dedup();
                if names.iter().any(|x| **x == "lunabot".to_owned() 
                                    || **x == "autopilot".to_owned() 
                                    || **x == "er16".to_owned() 
                                    || **x == "am31".to_owned()) { continue }

                let mut f = fs::OpenOptions::new()
                    .read(true)
                    .write(true)
                    .create(true).open("ignore.lst").unwrap();
                let mut content = String::new();
                let _ = f.read_to_string(&mut content);
                let ignored_names = content.split("\n").collect::<Vec<_>>();

                let names = names.iter().fold(Vec::new(),|mut acc,&x| {
                    match user.get_profile(x) {
                        Ok(x)   => if !ignored_names.iter().any(|y| *y == x.username) { acc.push(x.username) },
                        _       => ()
                    }
                    acc
                });

                let body = format!("Вас упомянул в посте <a href='{post_url}'>'{post_name}'\
                                       </a> пользователь <ls user='{user}' /> \n <a href='{comm_url}'>Ссылка</a> на комментарий",
                                       post_url     = format!("{}/blog/{}.html", HOST_URL, comm.post_id),
                                       post_name    = user.get_post("",comm.post_id).unwrap().title,
                                       user         = comm.author,
                                       comm_url     = format!("{}/blog/{}.html#comment{}",HOST_URL, comm.post_id, comm.id));
                if names.len() >= 1 {
                    let tid = user.add_talk(&names.iter().map(|x| x.as_str()).collect(), "Упоминание", &body).unwrap();
                    let _ = user.delete_talk(tid);
                }
                let cbody = if names.len() > 1 {
                    let mut c = format!("Сообщение об упоминании отправлено пользователям: {}",
                                        names.iter().fold(String::new(),|mut acc, x| { acc.push_str(&format!("<ls user='{}'>, ",x)); acc }));
                    c.pop(); c.pop();
                    c
                } else if names.len() == 1 {
                    format!("Сообщение об упоминании отправлено пользователю <ls user='{}'>",names[0])
                } else {
                    String::new()
                };

                if !cbody.is_empty() {
                    let _ = user.comment(comm.post_id, &cbody, comm.id, CommentType::Post);
                }
            }
        }
    }
}

pub fn dothing() {
    let mut user = TClient::new("", "").unwrap();
    loop {
        let comms = user.get_comments("").unwrap();
        check(&mut user, comms);
        thread::sleep(time::Duration::new(30,0))
    }
}
