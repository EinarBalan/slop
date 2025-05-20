import './App.css'
import likeIcon from './assets/like.svg';
import commentIcon from './assets/comment.svg';
import forwardIcon from './assets/forward.svg';
import backIcon from './assets/back.svg';
import robotIcon from './assets/robot.svg';
import dislikeIcon from './assets/dislike.svg';

function Feed({ title, content }: { title: string; content: string }) {
  return (
    <div id="feed">
      <h1>{title}</h1>
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

function Controls() {
  return (
    <div id="controls">
      <InteractionButton icon={likeIcon} onClick={() => console.log('Like')} />
      <InteractionButton icon={commentIcon} onClick={() => console.log('Comment')} />
      <InteractionButton icon={robotIcon} onClick={() => console.log('Robot')} />
      <InteractionButton icon={dislikeIcon} onClick={() => console.log('Dislike')} />
      <InteractionButton icon={backIcon} onClick={() => console.log('Back')} />
      <InteractionButton icon={forwardIcon} onClick={() => console.log('Forward')} />
      </div>
  )
}

function App() {

  return (
    <div id ="app">
      <Feed title="Title" content="content"/>
      <Controls />
    </div>
  )
}

export default App
