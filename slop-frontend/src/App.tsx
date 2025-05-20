import './App.css'
import likeIcon from './assets/like.svg';
import commentIcon from './assets/comment.svg';
import forwardIcon from './assets/forward.svg';
import backIcon from './assets/back.svg';
import robotIcon from './assets/robot.svg';
import dislikeIcon from './assets/dislike.svg';
import { useState, useEffect } from 'react';

interface Post {
  title: string;
  post_id: string;
  over_18: string;
  subreddit: string;
  link_flair_text: string;
  self_text: string;
}

function Feed({ title, content, subreddit }: { title: string; content: string; subreddit: string }) {
  return (
    <div id="feed">
      <h1>{title}</h1>
      <p className="subreddit">r/{subreddit}</p>
      <p>{content}</p>
    </div>
  )
}

function InteractionButton({ icon, onClick }: { icon: string, onClick: () => void }) {
  return (
    <button className="interaction-button" onClick={onClick}>
      <img src={icon} alt="icon" />
    </button>
  )
}

function Controls({ nextPost, prevPost }: { nextPost: () => void, prevPost: () => void }) {
  return (
    <div id="controls">
      <InteractionButton icon={likeIcon} onClick={() => console.log('Like')} />
      <InteractionButton icon={commentIcon} onClick={() => console.log('Comment')} />
      <InteractionButton icon={robotIcon} onClick={() => console.log('Robot')} />
      <InteractionButton icon={dislikeIcon} onClick={() => console.log('Dislike')} />
      <InteractionButton icon={backIcon} onClick={prevPost} />
      <InteractionButton icon={forwardIcon} onClick={nextPost} />
      </div>
  )
}

function App() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [currentPostIndex, setCurrentPostIndex] = useState(0);

  const nextPost = () => {
    if (currentPostIndex >= posts.length - 1) { // get next batch
      fetch('http://localhost:3000/batch')
        .then(response => response.json())
        .then(data => {
          setPosts(data.posts);
          setCurrentPostIndex(0);
        });
    } else {
      setCurrentPostIndex(currentPostIndex + 1);
    }
  }

  const prevPost = () => {
    if (currentPostIndex > 0) {
      setCurrentPostIndex(currentPostIndex - 1);
    }
  }

  useEffect(() => {
    fetch('http://localhost:3000/batch')
      .then(response => response.json())
      .then(data => {
        setPosts(data.posts);
        console.log(data.posts);
      });
  }, []);

  return (
    <div id ="app">
      <Feed 
        title={posts[currentPostIndex]?.title} 
        content={posts[currentPostIndex]?.self_text}
        subreddit={posts[currentPostIndex]?.subreddit}
      />
      <Controls nextPost={nextPost} prevPost={prevPost} />
    </div>
  )
}

export default App
